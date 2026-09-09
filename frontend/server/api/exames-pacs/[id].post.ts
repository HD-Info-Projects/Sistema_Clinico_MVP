export default defineEventHandler(async (event) => {
  const id = Number(getRouterParam(event, 'id'))
  if (!Number.isFinite(id) || id <= 0) {
    throw createError({ statusCode: 400, message: 'Exame inválido' })
  }

  try {
    return await flaskFetch(event, `/exames-pacs/${id}`, { method: 'POST' })
  } catch (error) {
    throwProxyError(error, 'Falha ao abrir viewer de imagem no backend Flask')
  }
})
