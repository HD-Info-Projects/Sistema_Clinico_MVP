<script setup lang="ts">
import { TextSelection } from '@tiptap/pm/state'
import { defu } from 'defu'
import type { EditorProps } from '@tiptap/pm/view'
import { useTextTransform } from '~/composables/useTextTransform'

const props = defineProps<{
  modelValue?: string
  placeholder?: string
  ui?: { root?: string, content?: string, base?: string }
  class?: string
}>()

const emit = defineEmits<{
  'update:modelValue': [value: string]
}>()

const { transformUpperCase, transformLowerCase, transformCapitalize } = useTextTransform()

const mergedUi = computed(() => {
  const merged = defu(props.ui ?? {}, { base: 'min-h-48 flex-1 overflow-y-auto' })
  return { ...merged, base: `${merged.base} *:my-2 [&_p]:leading-6` }
})

const editorRef = ref<{ editor: import('@tiptap/core').Editor | undefined }>()
let cleanupListener: (() => void) | undefined

const editorProps: EditorProps = {
  handleDOMEvents: {
    mousedown: (view, event) => {
      const end = view.state.doc.content.size
      if (end > 1) {
        const coords = view.coordsAtPos(end - 1)
        if (coords && event.clientY > coords.bottom) {
          view.dispatch(
            view.state.tr.setSelection(TextSelection.create(view.state.doc, end, end))
          )
          view.focus()
        }
      }
      return false
    }
  }
}

watch(() => editorRef.value?.editor, (editor) => {
  cleanupListener?.()
  if (!editor) return

  nextTick(() => {
    const view = editor.view
    const editorDom = view.dom
    const wrapper = editorDom.parentElement
    if (!wrapper) return

    const handleMouseDown = (event: MouseEvent) => {
      const target = event.target as Node
      if (editorDom === target || editorDom.contains(target)) return
      const { state } = view
      const end = state.doc.content.size
      view.dispatch(state.tr.setSelection(TextSelection.create(state.doc, end, end)))
      view.focus()
    }

    wrapper.addEventListener('mousedown', handleMouseDown)
    cleanupListener = () => wrapper.removeEventListener('mousedown', handleMouseDown)
  })
})

onUnmounted(() => {
  cleanupListener?.()
})
</script>

<template>
  <UEditor
    ref="editorRef"
    :model-value="modelValue"
    :placeholder="placeholder"
    :ui="mergedUi"
    :editor-props="editorProps"
    :class="props.class"
    v-bind="$attrs"
    @update:model-value="emit('update:modelValue', $event)"
  >
    <template #default="{ editor }">
      <div
        class="flex shrink-0 flex-wrap gap-1 overflow-x-auto border-b border-muted bg-neutral-50 p-2 dark:bg-neutral-900 rounded-t-lg"
        role="toolbar"
        aria-label="Formatação de texto"
      >
        <UButton
          icon="i-lucide-bold"
          aria-label="Negrito"
          :aria-pressed="editor?.isActive('bold')"
          size="xs"
          color="neutral"
          variant="ghost"
          :class="{ 'bg-primary/10 text-primary': editor?.isActive('bold') }"
          @click="void editor?.chain().focus().toggleBold().run()"
        />
        <UButton
          icon="i-lucide-italic"
          aria-label="Itálico"
          :aria-pressed="editor?.isActive('italic')"
          size="xs"
          color="neutral"
          variant="ghost"
          :class="{ 'bg-primary/10 text-primary': editor?.isActive('italic') }"
          @click="void editor?.chain().focus().toggleItalic().run()"
        />
        <UButton
          icon="i-lucide-strikethrough"
          aria-label="Tachado"
          :aria-pressed="editor?.isActive('strike')"
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
          aria-label="Título nível 1"
          :aria-pressed="editor?.isActive('heading', { level: 1 })"
          size="xs"
          color="neutral"
          variant="ghost"
          :class="{ 'bg-primary/10 text-primary': editor?.isActive('heading', { level: 1 }) }"
          @click="void editor?.chain().focus().toggleHeading({ level: 1 }).run()"
        />
        <UButton
          icon="i-lucide-heading-2"
          aria-label="Título nível 2"
          :aria-pressed="editor?.isActive('heading', { level: 2 })"
          size="xs"
          color="neutral"
          variant="ghost"
          :class="{ 'bg-primary/10 text-primary': editor?.isActive('heading', { level: 2 }) }"
          @click="void editor?.chain().focus().toggleHeading({ level: 2 }).run()"
        />
        <UButton
          icon="i-lucide-heading-3"
          aria-label="Título nível 3"
          :aria-pressed="editor?.isActive('heading', { level: 3 })"
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
          aria-label="Lista com marcadores"
          :aria-pressed="editor?.isActive('bulletList')"
          size="xs"
          color="neutral"
          variant="ghost"
          :class="{ 'bg-primary/10 text-primary': editor?.isActive('bulletList') }"
          @click="void editor?.chain().focus().toggleBulletList().run()"
        />
        <UButton
          icon="i-lucide-list-ordered"
          aria-label="Lista numerada"
          :aria-pressed="editor?.isActive('orderedList')"
          size="xs"
          color="neutral"
          variant="ghost"
          :class="{ 'bg-primary/10 text-primary': editor?.isActive('orderedList') }"
          @click="void editor?.chain().focus().toggleOrderedList().run()"
        />
        <UButton
          icon="i-lucide-text-quote"
          aria-label="Citação"
          :aria-pressed="editor?.isActive('blockquote')"
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
          aria-label="Desfazer"
          size="xs"
          color="neutral"
          variant="ghost"
          @click="void editor?.chain().focus().undo().run()"
        />
        <UButton
          icon="i-lucide-redo"
          aria-label="Refazer"
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
          aria-label="Converter para maiúsculas"
          size="xs"
          color="neutral"
          variant="ghost"
          @click="transformUpperCase(editor)"
        >
          <span class="font-semibold text-[10px]">AA</span>
        </UButton>
        <UButton
          aria-label="Converter para minúsculas"
          size="xs"
          color="neutral"
          variant="ghost"
          @click="transformLowerCase(editor)"
        >
          <span class="text-[10px]">aa</span>
        </UButton>
        <UButton
          aria-label="Capitalizar texto"
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
</template>
