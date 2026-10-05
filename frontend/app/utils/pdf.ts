export async function usePdfMake() {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const pdfMake: any = (await import('pdfmake/build/pdfmake')).default
  const vfs = (await import('pdfmake/build/vfs_fonts')).default
  pdfMake.vfs = vfs
  return pdfMake as { createPdf: (doc: Record<string, unknown>) => { download: (name: string) => void, open: (win?: Window | null) => void | Promise<void>, getBlob: (cb: (blob: Blob) => void) => void } }
}
