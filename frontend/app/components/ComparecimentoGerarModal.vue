<script setup lang="ts">
import type { AgendamentoComPaciente, Paciente } from '~/types'
import { buildAtestadoComparecimento } from '~/utils/pdf-documents'
import { usePdfMake } from '~/utils/pdf'

const props = defineProps<{
  paciente?: Paciente
  agendamento?: AgendamentoComPaciente | null
  dataAtendimento?: string
  cids?: string[]
}>()

const open = defineModel<boolean>('open', { default: false })

const agendamentosStore = useAgendamentosStore()
const auth = useAuthStore()
const toast = useToast()

const agendamento = computed(() => props.agendamento ?? agendamentosStore.emAtendimento ?? null)
const paciente = computed(() => props.paciente ?? agendamento.value?.paciente ?? null)
const tipoNome = ref<'paciente' | 'outro'>('paciente')
const outroNome = ref('')
const gerando = ref(false)

const opcoesNome = computed(() => [
  {
    label: 'Paciente',
    value: 'paciente',
    description: paciente.value?.nome ?? 'Paciente não informado'
  },
  {
    label: 'Outro',
    value: 'outro',
    description: 'Informe manualmente o nome que constará no documento.'
  }
])

const nomeComparecimento = computed(() => {
  if (tipoNome.value === 'outro') return outroNome.value.trim()
  return paciente.value?.nome.trim() ?? ''
})

function hojeIso() {
  const d = new Date()
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}

const dataAtendimentoPadrao = computed(() => props.dataAtendimento ?? agendamento.value?.data ?? hojeIso())

const podeImprimir = computed(() => Boolean(
  nomeComparecimento.value
  && dataAtendimentoPadrao.value
  && agendamento.value?.horario
))

watch(open, (isOpen) => {
  if (!isOpen) return
  tipoNome.value = 'paciente'
  outroNome.value = ''
})

function formatarDataPdf(data: string) {
  if (!data) return ''
  const dataNormalizada = /^\d{4}-\d{2}-\d{2}$/.test(data) ? `${data}T12:00:00` : data
  const valor = new Date(dataNormalizada)
  return Number.isNaN(valor.getTime()) ? data : valor.toLocaleDateString('pt-BR')
}

async function gerarPdf() {
  if (!podeImprimir.value || !agendamento.value) return

  gerando.value = true
  try {
    const pdfMake = await usePdfMake()
    const doc = await buildAtestadoComparecimento({
      paciente: nomeComparecimento.value,
      identificacao: tipoNome.value,
      cids: props.cids,
      data: formatarDataPdf(dataAtendimentoPadrao.value),
      horario: agendamento.value.horario.slice(0, 5),
      medico: auth.user?.nome,
      crm: auth.user?.crm,
      especialidade: auth.user?.especialidades?.join(', ')
    })

    open.value = false
    await nextTick()
    pdfMake.createPdf(doc).open()
  } catch {
    toast.add({
      title: 'Erro ao gerar comparecimento',
      description: 'Não foi possível gerar o documento para impressão.',
      color: 'error',
      icon: 'i-lucide-alert-circle'
    })
  } finally {
    gerando.value = false
  }
}
</script>

<template>
  <UModal
    v-model:open="open"
    :ui="{ content: 'max-h-dvh sm:max-h-[calc(100dvh-2rem)]', body: 'min-h-0 overflow-y-auto p-0', footer: 'shrink-0' }"
  >
    <template #header>
      <div class="flex items-center justify-between">
        <h2 class="text-lg font-semibold">
          Gerar Atestado de Comparecimento
        </h2>
        <UButton
          icon="i-lucide-x"
          aria-label="Fechar atestado"
          color="neutral"
          variant="ghost"
          @click="void (open = false)"
        />
      </div>
    </template>

    <template #body>
      <div class="space-y-5 p-4 sm:p-6">
        <UFormField label="Nome no documento">
          <URadioGroup
            v-model="tipoNome"
            :items="opcoesNome"
          />
        </UFormField>

        <UFormField
          v-if="tipoNome === 'outro'"
          label="Outro nome"
          required
        >
          <UInput
            v-model="outroNome"
            placeholder="Digite o nome completo"
            maxlength="255"
            autofocus
            class="w-full"
          />
        </UFormField>
      </div>
    </template>

    <template #footer>
      <div class="flex w-full flex-col-reverse gap-2 sm:flex-row sm:justify-between">
        <UButton
          label="Cancelar"
          color="neutral"
          variant="ghost"
          class="w-full justify-center sm:w-auto"
          @click="void (open = false)"
        />
        <UButton
          icon="i-lucide-printer"
          label="Imprimir"
          :disabled="!podeImprimir"
          :loading="gerando"
          class="w-full justify-center sm:w-auto"
          @click="gerarPdf"
        />
      </div>
    </template>
  </UModal>
</template>
