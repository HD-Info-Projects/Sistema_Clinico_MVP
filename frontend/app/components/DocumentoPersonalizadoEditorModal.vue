<script setup lang="ts">
import * as z from 'zod'
import type { FormSubmitEvent } from '@nuxt/ui'
import { salvarDocumentoPersonalizado } from '~/features/documentos/services/documentosService'
import type { AgendamentoComPaciente, DocumentoPersonalizado } from '~/types'

const props = defineProps<{
  agendamento?: AgendamentoComPaciente | null
  documento?: DocumentoPersonalizado | null
}>()

const emit = defineEmits<{
  saved: [documento: DocumentoPersonalizado]
  cancelled: []
}>()

const open = defineModel<boolean>('open', { default: false })
const toast = useToast()
const form = useTemplateRef('form')
const salvando = ref(false)
const state = reactive({ titulo: '', conteudo: '' })

const schema = z.object({
  titulo: z.string().trim().min(1, 'Informe o título do documento.'),
  conteudo: z.string().refine(
    value => value.replace(/<[^>]*>/g, '').trim().length > 0,
    'Informe o texto do documento.'
  )
})

type Schema = z.output<typeof schema>

const podeEditar = computed(() => props.documento?.podeEditar ?? true)

watch(
  () => [open.value, props.documento?.id, props.documento?.updatedAt] as const,
  ([isOpen]) => {
    if (!isOpen) return
    state.titulo = props.documento?.titulo ?? ''
    state.conteudo = props.documento?.conteudo ?? ''
  },
  { immediate: true }
)

async function salvar() {
  if (!props.agendamento || !podeEditar.value) return
  const validation = await form.value?.validate({})
  if (!validation) return

  salvando.value = true
  try {
    const documento = await salvarDocumentoPersonalizado(
      props.agendamento.id,
      { titulo: state.titulo.trim(), conteudo: state.conteudo },
      props.documento?.id
    )
    emit('saved', documento)
    open.value = false
  } catch {
    toast.add({
      title: 'Erro ao salvar documento',
      description: 'Não foi possível salvar o documento personalizado.',
      color: 'error',
      icon: 'i-lucide-alert-circle'
    })
  } finally {
    salvando.value = false
  }
}

function onSubmit(_event: FormSubmitEvent<Schema>) {
  void salvar()
}

function cancelar() {
  open.value = false
  emit('cancelled')
}
</script>

<template>
  <UModal
    v-model:open="open"
    :ui="{ content: 'h-dvh max-w-4xl', body: 'flex min-h-0 flex-1  flex-col overflow-y-auto p-0', footer: 'shrink-0' }"
  >
    <template #header>
      <div class="flex w-full items-center justify-between gap-3">
        <div class="min-w-0">
          <h2 class="text-lg font-semibold">
            {{ documento ? 'Editar documento médico' : 'Criar documento médico' }}
          </h2>
          <p class="mt-0.5 text-sm text-muted">
            Texto livre para impressão com cabeçalho e assinatura padrão
          </p>
        </div>
        <UButton
          icon="i-lucide-x"
          aria-label="Fechar editor de documento"
          color="neutral"
          variant="ghost"
          @click="cancelar"
        />
      </div>
    </template>

    <template #body>
      <UForm
        id="documento-personalizado-form"
        ref="form"
        :schema="schema"
        :state="state"
        class="flex min-h-0 flex-1 flex-col gap-5 p-4 sm:p-6"
        @submit="onSubmit"
      >
        <UFormField
          name="titulo"
          label="Título do documento"
          required
          class="shrink-0"
        >
          <UInput
            v-model="state.titulo"
            placeholder="Ex.: Relatório médico"
            :disabled="!podeEditar"
            size="lg"
            class="w-full"
          />
        </UFormField>

        <UFormField
          name="conteudo"
          label="Texto do documento"
          required
          class="flex min-h-0 flex-1 flex-col"
        >
          <EditorRichText
            v-model="state.conteudo"
            placeholder="Digite o conteúdo do documento..."
            :ui="{ base: 'min-h-72 max-h-none' }"
            :class="podeEditar
              ? 'flex min-h-0 flex-1 flex-col'
              : 'flex min-h-0 flex-1 flex-col pointer-events-none opacity-70'"
          />
        </UFormField>
      </UForm>
    </template>

    <template #footer>
      <div class="flex w-full flex-col-reverse gap-2 sm:flex-row sm:justify-end">
        <UButton
          label="Cancelar"
          color="neutral"
          variant="ghost"
          class="w-full justify-center sm:w-auto"
          @click="cancelar"
        />
        <UButton
          v-if="podeEditar"
          type="submit"
          form="documento-personalizado-form"
          icon="i-lucide-save"
          label="Salvar"
          :loading="salvando"
          class="w-full justify-center sm:w-auto"
        />
      </div>
    </template>
  </UModal>
</template>
