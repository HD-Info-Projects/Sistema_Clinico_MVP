export default defineEventHandler(async (event) => {
  const id = getRouterParam(event, 'id')
  if (!id) throw createError({ statusCode: 400, statusMessage: 'id obrigatório' })

  try {
    return await getClinicaPublica(event, id)
  } catch (error) {
    throwProxyError(error, 'Falha ao carregar unidade')
  }
})
