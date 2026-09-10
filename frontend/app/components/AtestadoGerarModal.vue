<script setup lang="ts">
import type { AgendamentoComPaciente, AtestadoDocumentoDados, DocumentoMedico, Paciente } from '~/types'
import { usePdfMake } from '~/utils/pdf'
import { buildAtestado } from '~/utils/pdf-documents'

const props = defineProps<{
  paciente?: Paciente
  agendamento?: AgendamentoComPaciente | null
  dataAtendimento?: string
  documento?: DocumentoMedico | null
}>()

const emit = defineEmits<{
  saved: [documento: DocumentoMedico]
}>()

const open = defineModel<boolean>('open', { default: false })

const agendamentosStore = useAgendamentosStore()
const toast = useToast()

const paciente = computed(() => props.paciente ?? props.agendamento?.paciente ?? agendamentosStore.emAtendimento?.paciente ?? null)
const medSpdataAtendimentoId = computed(() => props.agendamento?.id ?? agendamentosStore.emAtendimento?.id ?? null)
const podeEditar = computed(() => props.documento?.podeEditar ?? true)

function hojeIso() {
  const d = new Date()
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}

const dataAtendimentoPadrao = computed(() => props.dataAtendimento ?? props.agendamento?.data ?? hojeIso())

const data = ref(dataAtendimentoPadrao.value)
const dias = ref<number | null>(null)
const salvando = ref(false)

function preencherFormulario() {
  const dados = props.documento?.tipoDocumento === 'ATESTADO'
    ? props.documento.dados as AtestadoDocumentoDados
    : null

  data.value = dados?.data_inicio ?? dataAtendimentoPadrao.value
  dias.value = dados?.dias_afastamento ? Number(dados.dias_afastamento) : null
}

watch(
  () => [open.value, props.documento?.id, props.documento?.updatedAt, dataAtendimentoPadrao.value] as const,
  ([isOpen]) => {
    if (isOpen) preencherFormulario()
  },
  { immediate: true }
)

const TEXTO_ATESTADO = `Atesto que o(a) paciente {nome} esteve sob meus cuidados médicos, necessitando de {dias} dias de repouso/afastamento a partir de {data}.`

function formatarDataPdf(dataISO: string) {
  if (!dataISO) return ''
  return new Date(dataISO + 'T12:00:00').toLocaleDateString('pt-BR')
}

function textoAtestado(dados: AtestadoDocumentoDados) {
  return TEXTO_ATESTADO
    .replace('{nome}', paciente.value?.nome ?? 'Paciente')
    .replace('{dias}', String(dados.dias_afastamento))
    .replace('{data}', formatarDataPdf(dados.data_inicio))
}

const podeEnviar = computed(() => {
  if (!podeEditar.value) return Boolean(props.documento)
  return Boolean(medSpdataAtendimentoId.value && data.value && dias.value && dias.value > 0)
})

const botaoLabel = computed(() => podeEditar.value ? 'Salvar e Imprimir' : 'Imprimir')

async function gerarPdf(documento: DocumentoMedico) {
  if (documento.tipoDocumento !== 'ATESTADO') return

  const dados = documento.dados as AtestadoDocumentoDados
  const pdfMake = await usePdfMake()
  const doc = await buildAtestado({
    paciente: paciente.value?.nome ?? 'Paciente',
    conteudoHtml: `<p>${textoAtestado(dados)}</p>`,
    medico: dados.medico ?? undefined,
    crm: dados.crm ?? undefined,
    especialidade: dados.especialidade ?? undefined
  })
  pdfMake.createPdf(doc).open()
}

async function fecharEAbrirPdf(documento: DocumentoMedico) {
  open.value = false
  await nextTick()
  await gerarPdf(documento)
}

async function salvarEImprimir() {
  if (!podeEnviar.value) return

  if (!podeEditar.value && props.documento) {
    await fecharEAbrirPdf(props.documento)
    return
  }

  salvando.value = true
  try {
    const documento = await $fetch<DocumentoMedico>(`/api/documentos-medicos/${medSpdataAtendimentoId.value}/ATESTADO`, {
      method: 'PUT',
      body: {
        dados: {
          data_inicio: data.value,
          dias_afastamento: dias.value
        }
      }
    })

    emit('saved', documento)
    await fecharEAbrirPdf(documento)
  } catch {
    toast.add({
      title: 'Erro ao salvar atestado',
      description: 'Não foi possível salvar o documento médico.',
      color: 'error',
      icon: 'i-lucide-alert-circle'
    })
  } finally {
    salvando.value = false
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
          Gerar Atestado Médico
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
      <div class="space-y-4 p-4 sm:p-6">
        <UFormField label="Paciente">
          <UInput
            :model-value="paciente?.nome ?? '—'"
            disabled
            class="w-full"
          />
        </UFormField>

        <UFormField label="Data de início">
          <UInput
            v-model="data"
            type="date"
            :disabled="!podeEditar"
            class="w-full"
          />
        </UFormField>

        <UFormField label="Dias de afastamento">
          <UInput
            v-model.number="dias"
            type="number"
            min="1"
            placeholder="Ex: 7"
            :disabled="!podeEditar"
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
          :label="botaoLabel"
          :disabled="!podeEnviar"
          :loading="salvando"
          class="w-full justify-center sm:w-auto"
          @click="salvarEImprimir"
        />
      </div>
    </template>
  </UModal>
</template>
