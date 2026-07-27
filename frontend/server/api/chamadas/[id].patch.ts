export default defineEventHandler(async (event) => {
  await requireRole(event, ['medico', 'recepcao'])
  const id = Number(getRouterParam(event, 'id'))
  const body = await readBody<{ status?: string }>(event)

  if (!Number.isFinite(id) || id <= 0) {
    throw createError({ statusCode: 400, statusMessage: 'id inválido' })
  }

  if (body.status !== 'concluido' && body.status !== 'cancelado') {
    throw createError({ statusCode: 400, statusMessage: 'Status inválido' })
  }

  const chamado = atualizarChamadoStatus(id, body.status)
  if (!chamado) {
    throw createError({ statusCode: 404, statusMessage: 'Chamado não encontrado' })
  }

  return chamado
})
