export default defineEventHandler(async (event) => {
  const id = Number(getRouterParam(event, 'id'))
  if (!Number.isFinite(id) || id <= 0) {
    throw createError({ statusCode: 400, message: 'Paciente inválido' })
  }

  try {
    return await flaskFetch(event, `/exames-pacs/paciente/${id}`)
  } catch (error) {
    throwProxyError(error, 'Falha ao carregar resultados de exames no backend Flask')
  }
})
