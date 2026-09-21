declare module 'html-to-pdfmake' {
  type PdfMakeContent = Record<string, unknown>
  const htmlToPdfmake: (html: string, options?: {
    window?: Window
    removeExtraBlanks?: boolean
    defaultStyles?: Record<string, Record<string, unknown>>
  }) => PdfMakeContent[]
  export default htmlToPdfmake
}
