export default defineEventHandler(async (event) => {
  const id = getRouterParam(event, 'id')
  if (!id) throw createError({ statusCode: 400, statusMessage: 'id obrigatório' })

  try {
    return await getClinicaPublica(id)
  } catch {
    throw createError({ statusCode: 404, statusMessage: 'Unidade não encontrada' })
  }
})
