import type { Editor } from '@tiptap/core'

export function useTextTransform() {
  function transform(editor: Editor, fn: (text: string) => string) {
    const { state } = editor
    const { from, to } = state.selection
    if (from === to) return

    const text = state.doc.textBetween(from, to)
    if (!text) return

    const transformed = fn(text)
    if (transformed === text) return

    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    let firstMark: any = null
    state.doc.nodesBetween(from, to, (node) => {
      if (node.isText && !firstMark) {
        firstMark = node.marks
      }
    })

    editor
      .chain()
      .focus()
      .command(({ tr }) => {
        tr.replaceWith(from, to, state.schema.text(transformed, firstMark ?? undefined))
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
