import type { Editor } from '@tiptap/core'

export function useTextTransform() {
  function transform(editor: Editor, fn: (text: string) => string) {
    const { state } = editor
    const { from, to } = state.selection
    if (from === to) return

    type Edit = { from: number, to: number, text: string }
    const edits: Edit[] = []

    state.doc.nodesBetween(from, to, (node, pos) => {
      if (!node.isText) return
      const start = Math.max(from, pos)
      const end = Math.min(to, pos + node.nodeSize)
      const slice = node.text?.slice(start - pos, end - pos) ?? ''
      const newText = fn(slice)
      if (newText !== slice) {
        edits.push({ from: start, to: end, text: newText })
      }
    })

    if (edits.length === 0) return

    editor
      .chain()
      .focus()
      .command(({ tr }) => {
        for (const edit of edits.sort((a, b) => b.from - a.from)) {
          tr.insertText(edit.text, edit.from, edit.to)
        }
        return true
      })
      .run()
  }

  function transformUpperCase(editor: Editor) {
    transform(editor, t => t.toUpperCase())
  }

  function transformLowerCase(editor: Editor) {
    transform(editor, t => t.toLowerCase())
  }

  function transformCapitalize(editor: Editor) {
    transform(editor, t => t.replace(/\b\w/g, c => c.toUpperCase()))
  }

  return { transformUpperCase, transformLowerCase, transformCapitalize }
}
