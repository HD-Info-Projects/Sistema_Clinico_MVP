type LaudoExamePacs = {
  contentType?: string
  filename?: string
  base64: string
}

function nomeArquivoSeguro(filename: string | undefined, id: number) {
  const nome = String(filename || `laudo-exame-${id}.pdf`).replace(/[\\/\r\n"]/g, '')
  return nome || `laudo-exame-${id}.pdf`
}

export default defineEventHandler(async (event) => {
  const id = Number(getRouterParam(event, 'id'))
  if (!Number.isFinite(id) || id <= 0) {
    throw createError({ statusCode: 400, message: 'Exame inválido' })
  }

  try {
    const laudo = await flaskFetch<LaudoExamePacs>(event, `/exames-pacs/${id}/laudo`)
    const pdf = Buffer.from(laudo.base64, 'base64')
    const contentType = laudo.contentType || 'application/pdf'
    const filename = nomeArquivoSeguro(laudo.filename, id)

    setResponseHeader(event, 'Content-Type', contentType)
    setResponseHeader(event, 'Content-Disposition', `inline; filename="${filename}"`)
    setResponseHeader(event, 'Content-Length', pdf.length)
    setResponseHeader(event, 'Cache-Control', 'no-store, private')
    setResponseHeader(event, 'Pragma', 'no-cache')
    setResponseHeader(event, 'X-Content-Type-Options', 'nosniff')

    return pdf
  } catch (error) {
    throwProxyError(error, 'Falha ao carregar PDF do laudo no backend Flask')
  }
})
