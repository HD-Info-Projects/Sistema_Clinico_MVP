export default defineEventHandler(async (event) => {
  const id = getRouterParam(event, 'id')
  if (!id) {
    throw createError({ statusCode: 400, statusMessage: 'id é obrigatório' })
  }

  await flaskFetch(event, `/padrao_medico_anamnese/deletar/${id}`, {
    params: medicoAlvoParams(event),
    method: 'DELETE'
  })

  return { success: true }
})
