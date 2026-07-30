<script setup lang="ts">
import type { EditorView, EditorProps } from '@tiptap/pm/view'
import { TextSelection } from '@tiptap/pm/state'
import { defu } from 'defu'
import { useTextTransform } from '~/composables/useTextTransform'

const props = defineProps<{
  modelValue?: string
  placeholder?: string
  editorProps?: EditorProps
  ui?: { root?: string, content?: string, base?: string }
  class?: string
}>()

const emit = defineEmits<{
  'update:modelValue': [value: string]
}>()

const { transformUpperCase, transformLowerCase, transformCapitalize } = useTextTransform()

const defaultEditorProps: EditorProps = {
  handleDOMEvents: {
    mousedown: (view: EditorView, event: MouseEvent) => {
      if ((event.target as HTMLElement) === view.dom) {
        const { state } = view
        const end = state.doc.content.size
        view.dispatch(state.tr.setSelection(TextSelection.near(state.doc.resolve(end), -1)))
        view.focus()
        return true
      }
      return false
    }
  }
}

const mergedEditorProps = computed<EditorProps>(() => defu(props.editorProps ?? {}, defaultEditorProps))
const mergedUi = computed(() => defu(props.ui ?? {}, { base: 'min-h-full' }))
</script>

<template>
  <UEditor
    :model-value="modelValue"
    :placeholder="placeholder"
    :ui="mergedUi"
    :editor-props="mergedEditorProps"
    :class="props.class"
    v-bind="$attrs"
    @update:model-value="emit('update:modelValue', $event)"
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
</template>
