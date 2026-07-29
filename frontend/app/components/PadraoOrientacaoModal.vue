<script setup lang="ts">
import type { PadraoOrientacaoExame } from '~/types'

const props = defineProps<{
  padrao?: PadraoOrientacaoExame | null
}>()

const open = defineModel<boolean>('open', { default: false })

const padroesOrientacoesStore = usePadroesOrientacoesStore()
const { transformUpperCase, transformLowerCase, transformCapitalize } = useTextTransform()

const nome = ref('')
const conteudo = ref('')
const saving = ref(false)

watch(open, (isOpen) => {
  if (isOpen) {
    nome.value = props.padrao?.nome ?? ''
    conteudo.value = props.padrao?.conteudo ?? ''
  }
}, { immediate: true })

async function salvar() {
  if (!nome.value.trim()) return
  saving.value = true
  try {
    const data = {
      nome: nome.value.trim(),
      conteudo: conteudo.value
    }
    if (props.padrao) {
      await padroesOrientacoesStore.atualizar(props.padrao.id, data)
    } else {
      await padroesOrientacoesStore.criar(data)
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
    fullscreen
  >
    <template #header>
      <div class="flex items-center justify-between w-full">
        <div>
          <h2 class="text-lg font-semibold">
            {{ padrao ? 'Editar' : 'Novo' }} Padrão de Orientação
          </h2>
          <p class="text-sm text-muted mt-0.5">
            Configure o nome e o conteúdo da orientação de exame
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
        <div class="space-y-1 flex flex-col">
          <label class="text-sm font-medium">Nome do modelo</label>
          <UInput
            v-model="nome"
            placeholder="Ex: Orientação para jejum"
            size="lg"
          />
        </div>

        <div class="space-y-1 flex flex-col grow">
          <label class="text-sm font-medium">Conteúdo da orientação</label>
          <UEditor
            v-model="conteudo"
            content-type="html"
            placeholder="Descreva o padrão de orientação..."
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
          label="Salvar"
          :loading="saving"
          :disabled="!nome.trim()"
          @click="salvar"
        />
      </div>
    </template>
  </UModal>
</template>
