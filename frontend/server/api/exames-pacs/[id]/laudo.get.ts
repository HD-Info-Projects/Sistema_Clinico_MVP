export default defineEventHandler(async (event) => {
  const id = Number(getRouterParam(event, 'id'))
  if (!Number.isFinite(id) || id <= 0) {
    throw createError({ statusCode: 400, message: 'Exame inválido' })
  }

  try {
    setResponseHeader(event, 'Cache-Control', 'no-store, private')
    setResponseHeader(event, 'Pragma', 'no-cache')
    setResponseHeader(event, 'X-Content-Type-Options', 'nosniff')
    return await flaskFetch(event, `/exames-pacs/${id}/laudo`)
  } catch (error) {
    throwProxyError(error, 'Falha ao carregar laudo do exame no backend Flask')
  }
})
