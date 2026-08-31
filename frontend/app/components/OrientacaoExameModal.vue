<script setup lang="ts">
import type { AgendamentoComPaciente, ExameSelecionado, Paciente, PadraoOrientacaoExame } from '~/types'

const props = defineProps<{
  paciente?: Paciente
  exame?: ExameSelecionado | null
  agendamento?: AgendamentoComPaciente | null
  dataAtendimento?: string
}>()

const emit = defineEmits<{
  saved: [orientacao: string]
}>()

const open = defineModel<boolean>('open', { default: false })

const agendamentosStore = useAgendamentosStore()
const padroesOrientacoesStore = usePadroesOrientacoesStore()

const paciente = computed(() => props.paciente ?? props.agendamento?.paciente ?? agendamentosStore.emAtendimento?.paciente ?? null)
const orientacaoTexto = ref('')
const padraoOrientacaoSelected = ref<{ label: string, value: PadraoOrientacaoExame }>()

onMounted(() => {
  padroesOrientacoesStore.fetchAll()
})

watch(
  () => [open.value, props.exame?.nome, props.exame?.orientacao] as const,
  ([isOpen]) => {
    if (!isOpen) return
    orientacaoTexto.value = props.exame?.orientacao ?? ''
    padraoOrientacaoSelected.value = undefined
  },
  { immediate: true }
)

function inserirPadraoOrientacao() {
  if (!padraoOrientacaoSelected.value) return
  orientacaoTexto.value += padraoOrientacaoSelected.value.value.conteudo
  padraoOrientacaoSelected.value = undefined
}

function salvar() {
  emit('saved', orientacaoTexto.value)
  open.value = false
}
</script>

<template>
  <UModal
    v-model:open="open"
    fullscreen
    :ui="{ content: 'h-dvh', body: 'flex min-h-0 flex-1 flex-col overflow-y-auto p-0', footer: 'shrink-0' }"
  >
    <template #header>
      <div class="flex items-center justify-between w-full">
        <div>
          <h2 class="text-lg font-semibold">
            Orientação do Exame
          </h2>
          <p class="text-sm text-muted mt-0.5">
            {{ exame?.nome ?? 'Exame não selecionado' }}
          </p>
        </div>
        <UButton
          icon="i-lucide-x"
          aria-label="Fechar orientação do exame"
          color="neutral"
          variant="ghost"
          @click="void (open = false)"
        />
      </div>
    </template>

    <template #body>
      <div class="flex min-h-0 flex-1 flex-col space-y-6 p-4 sm:p-6">
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <UFormField label="Paciente">
            <UInput
              :model-value="paciente?.nome ?? '—'"
              disabled
              class="w-full"
            />
          </UFormField>

          <UFormField label="Exame">
            <UInput
              :model-value="exame?.nome ?? '—'"
              disabled
              class="w-full"
            />
          </UFormField>
        </div>

        <div class="flex shrink-0 flex-col gap-2 sm:flex-row">
          <UInputMenu
            v-model="padraoOrientacaoSelected"
            :items="padroesOrientacoesStore.padroes.map(p => ({ label: p.nome, value: p }))"
            searchable
            placeholder="Selecionar padrão de orientação..."
            class="flex-1"
          />
          <UButton
            icon="i-lucide-copy-plus"
            label="Inserir Padrão"
            color="secondary"
            :disabled="!padraoOrientacaoSelected"
            @click="inserirPadraoOrientacao"
          />
        </div>

        <div class="flex min-h-0 flex-1 flex-col space-y-1">
          <label class="text-sm font-medium">Texto da orientação</label>
          <EditorRichText
            v-model="orientacaoTexto"
            placeholder="Descreva a orientação para este exame..."
            class="flex min-h-72 flex-1 flex-col"
          />
        </div>
      </div>
    </template>

    <template #footer>
      <div class="flex w-full flex-col-reverse gap-2 sm:flex-row sm:items-center sm:justify-end">
        <UButton
          label="Cancelar"
          color="neutral"
          variant="ghost"
          class="w-full justify-center sm:w-auto"
          @click="void (open = false)"
        />
        <UButton
          icon="i-lucide-save"
          label="Salvar"
          class="w-full justify-center sm:w-auto"
          @click="salvar"
        />
      </div>
    </template>
  </UModal>
</template>
