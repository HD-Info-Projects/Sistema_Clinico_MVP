<script setup lang="ts">
import type { AgendamentoComPaciente, ExameSelecionado, Paciente, PadraoOrientacaoExame } from '~/types'
import { useTextTransform } from '~/composables/useTextTransform'

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
const { transformUpperCase, transformLowerCase, transformCapitalize } = useTextTransform()

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
          color="neutral"
          variant="ghost"
          @click="void (open = false)"
        />
      </div>
    </template>

    <template #body>
      <div class="h-full overflow-y-auto p-6 space-y-6">
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

        <div class="shrink-0 flex gap-2">
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

        <div class="space-y-1 flex flex-col grow min-h-112">
          <label class="text-sm font-medium">Texto da orientação</label>
          <UEditor
            v-model="orientacaoTexto"
            content-type="html"
            placeholder="Descreva a orientação para este exame..."
            class="grow flex flex-col min-h-96"
          >
            <template #default="{ editor }">
              <div class="flex flex-wrap gap-1 p-2 border-b border-muted bg-neutral-50 dark:bg-neutral-900 rounded-t-lg">
                <UButton
                  icon="i-lucide-bold"
                  size="xs"
                  color="neutral"
                  variant="ghost"
                  :class="{ 'bg-primary/10 text-primary': editor?.isActive('bold') }"
                  @click="void editor?.chain().focus().toggleBold().run()"
                />
                <UButton
                  icon="i-lucide-italic"
                  size="xs"
                  color="neutral"
                  variant="ghost"
                  :class="{ 'bg-primary/10 text-primary': editor?.isActive('italic') }"
                  @click="void editor?.chain().focus().toggleItalic().run()"
                />
                <UButton
                  icon="i-lucide-strikethrough"
                  size="xs"
                  color="neutral"
                  variant="ghost"
                  :class="{ 'bg-primary/10 text-primary': editor?.isActive('strike') }"
                  @click="void editor?.chain().focus().toggleStrike().run()"
                />
                <USeparator
                  orientation="vertical"
                  class="h-6"
                />
                <UButton
                  icon="i-lucide-heading-1"
                  size="xs"
                  color="neutral"
                  variant="ghost"
                  :class="{ 'bg-primary/10 text-primary': editor?.isActive('heading', { level: 1 }) }"
                  @click="void editor?.chain().focus().toggleHeading({ level: 1 }).run()"
                />
                <UButton
                  icon="i-lucide-heading-2"
                  size="xs"
                  color="neutral"
                  variant="ghost"
                  :class="{ 'bg-primary/10 text-primary': editor?.isActive('heading', { level: 2 }) }"
                  @click="void editor?.chain().focus().toggleHeading({ level: 2 }).run()"
                />
                <UButton
                  icon="i-lucide-heading-3"
                  size="xs"
                  color="neutral"
                  variant="ghost"
                  :class="{ 'bg-primary/10 text-primary': editor?.isActive('heading', { level: 3 }) }"
                  @click="void editor?.chain().focus().toggleHeading({ level: 3 }).run()"
                />
                <USeparator
                  orientation="vertical"
                  class="h-6"
                />
                <UButton
                  icon="i-lucide-list"
                  size="xs"
                  color="neutral"
                  variant="ghost"
                  :class="{ 'bg-primary/10 text-primary': editor?.isActive('bulletList') }"
                  @click="void editor?.chain().focus().toggleBulletList().run()"
                />
                <UButton
                  icon="i-lucide-list-ordered"
                  size="xs"
                  color="neutral"
                  variant="ghost"
                  :class="{ 'bg-primary/10 text-primary': editor?.isActive('orderedList') }"
                  @click="void editor?.chain().focus().toggleOrderedList().run()"
                />
                <UButton
                  icon="i-lucide-text-quote"
                  size="xs"
                  color="neutral"
                  variant="ghost"
                  :class="{ 'bg-primary/10 text-primary': editor?.isActive('blockquote') }"
                  @click="void editor?.chain().focus().toggleBlockquote().run()"
                />
                <USeparator
                  orientation="vertical"
                  class="h-6"
                />
                <UButton
                  icon="i-lucide-undo"
                  size="xs"
                  color="neutral"
                  variant="ghost"
                  @click="void editor?.chain().focus().undo().run()"
                />
                <UButton
                  icon="i-lucide-redo"
                  size="xs"
                  color="neutral"
                  variant="ghost"
                  :class="{ 'bg-primary/10 text-primary': editor?.isActive('redo') }"
                  @click="void editor?.chain().focus().redo().run()"
                />
                <USeparator
                  orientation="vertical"
                  class="h-6"
                />
                <UButton
                  size="xs"
                  color="neutral"
                  variant="ghost"
                  @click="transformUpperCase(editor)"
                >
                  <span class="font-semibold text-[10px]">AA</span>
                </UButton>
                <UButton
                  size="xs"
                  color="neutral"
                  variant="ghost"
                  @click="transformLowerCase(editor)"
                >
                  <span class="text-[10px]">aa</span>
                </UButton>
                <UButton
                  size="xs"
                  color="neutral"
                  variant="ghost"
                  @click="transformCapitalize(editor)"
                >
                  <span class="text-[10px]">Aa</span>
                </UButton>
              </div>
            </template>
          </UEditor>
        </div>
      </div>
    </template>

    <template #footer>
      <div class="flex items-center justify-end gap-2 w-full">
        <UButton
          label="Cancelar"
          color="neutral"
          variant="ghost"
          @click="void (open = false)"
        />
        <UButton
          icon="i-lucide-save"
          label="Salvar"
          @click="salvar"
        />
      </div>
    </template>
  </UModal>
</template>
