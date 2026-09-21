<script setup lang="ts">
import * as z from 'zod'
import type { FormSubmitEvent } from '@nuxt/ui'
import type { PadraoDocumentoMedico } from '~/types'

const props = defineProps<{
  medicoId?: number | null
  padrao?: PadraoDocumentoMedico | null
}>()

const open = defineModel<boolean>('open', { default: false })
const padroesStore = usePadroesDocumentosStore()
const form = useTemplateRef('form')
const saving = ref(false)
const state = reactive({ nome: '', titulo: '', conteudo: '' })

const schema = z.object({
  nome: z.string().trim().min(1, 'Informe o nome do padrão.'),
  titulo: z.string().trim().min(1, 'Informe o título do documento.'),
  conteudo: z.string().refine(
    value => value.replace(/<[^>]*>/g, '').replace(/&nbsp;/gi, ' ').trim().length > 0,
    'Informe o conteúdo do documento.'
  )
})

type Schema = z.output<typeof schema>

watch(
  () => [open.value, props.padrao?.id] as const,
  ([isOpen]) => {
    if (!isOpen) return
    state.nome = props.padrao?.nome ?? ''
    state.titulo = props.padrao?.titulo ?? ''
    state.conteudo = props.padrao?.conteudo ?? ''
  },
  { immediate: true }
)

async function salvar(_event: FormSubmitEvent<Schema>) {
  const validation = await form.value?.validate({})
  if (!validation) return
  saving.value = true
  try {
    const data = {
      nome: state.nome.trim(),
      titulo: state.titulo.trim(),
      conteudo: state.conteudo
    }
    if (props.padrao) {
      await padroesStore.atualizar(props.padrao.id, data, props.medicoId ?? undefined)
    } else {
      await padroesStore.criar(data, props.medicoId ?? undefined)
    }
    open.value = false
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <UModal
    v-model:open="open"
    :ui="{ content: 'h-dvh max-w-4xl', body: 'flex min-h-0 flex-1 flex-col overflow-y-auto p-0', footer: 'shrink-0' }"
  >
    <template #header>
      <div class="flex w-full items-center justify-between gap-3">
        <div class="min-w-0">
          <h2 class="text-lg font-semibold">
            {{ padrao ? 'Editar' : 'Novo' }} padrão de documento médico
          </h2>
          <p class="mt-0.5 text-sm text-muted">
            Configure o nome, título e conteúdo reutilizável do documento
          </p>
        </div>
        <UButton
          icon="i-lucide-x"
          aria-label="Fechar padrão de documento médico"
          color="neutral"
          variant="ghost"
          @click="open = false"
        />
      </div>
    </template>

    <template #body>
      <UForm
        id="padrao-documento-medico-form"
        ref="form"
        :schema="schema"
        :state="state"
        class="flex min-h-0 flex-1 flex-col gap-5 p-4 sm:p-6"
        @submit="salvar"
      >
        <div class="grid shrink-0 grid-cols-1 gap-4 md:grid-cols-2">
          <UFormField
            name="nome"
            label="Nome do padrão"
            required
          >
            <UInput
              v-model="state.nome"
              placeholder="Ex.: Relatório de alta"
              size="lg"
              class="w-full"
            />
          </UFormField>
          <UFormField
            name="titulo"
            label="Título do documento"
            required
          >
            <UInput
              v-model="state.titulo"
              placeholder="Ex.: RELATÓRIO MÉDICO"
              size="lg"
              class="w-full"
            />
          </UFormField>
        </div>

        <UFormField
          name="conteudo"
          label="Conteúdo do documento"
          required
          class="flex min-h-0 flex-1 flex-col"
        >
          <EditorRichText
            v-model="state.conteudo"
            placeholder="Digite o conteúdo do padrão..."
            :ui="{ base: 'min-h-72 max-h-none' }"
            class="flex min-h-0 flex-1 flex-col"
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
          @click="open = false"
        />
        <UButton
          type="submit"
          form="padrao-documento-medico-form"
          icon="i-lucide-save"
          label="Salvar"
          :loading="saving"
          class="w-full justify-center sm:w-auto"
        />
      </div>
    </template>
  </UModal>
</template>
