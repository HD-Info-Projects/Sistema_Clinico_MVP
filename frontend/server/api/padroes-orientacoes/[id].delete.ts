export default defineEventHandler(async (event) => {
  const id = getRouterParam(event, 'id')
  if (!id) {
    throw createError({ statusCode: 400, statusMessage: 'id é obrigatório' })
  }

  await flaskFetch(event, `/padrao_medico_orientacao_exame/deletar/${id}`, {
    params: medicoAlvoParams(event),
    method: 'DELETE'
  })

  return { ok: true }
})
