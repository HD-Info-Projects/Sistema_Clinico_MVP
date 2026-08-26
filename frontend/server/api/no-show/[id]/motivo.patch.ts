export default defineEventHandler(async (event) => {
  const id = Number(getRouterParam(event, 'id'))
  if (!Number.isInteger(id) || id <= 0) {
    throw createError({ statusCode: 400, statusMessage: 'No-show inválido' })
  }

  const body = await readBody<{ motivo?: string }>(event)
  const motivo = String(body?.motivo ?? '').trim()
  const validMotivos = ['esquecimento', 'transporte', 'outros']

  if (!validMotivos.includes(motivo)) {
    throw createError({ statusCode: 400, statusMessage: 'Motivo da falta inválido' })
  }

  try {
    return await flaskFetch<{ id: number, motivo: string }>(event, `/no_show/${id}/motivo`, {
      method: 'PATCH',
      body: { motivo }
    })
  } catch (error) {
    const fetchError = error as { status?: number, statusCode?: number, response?: { status?: number } }
    const status = fetchError.response?.status || fetchError.statusCode || fetchError.status || 502

    throw createError({
      statusCode: status,
      message: status === 401 ? 'Não autorizado' : status === 403 ? 'Acesso negado' : 'Falha ao registrar motivo do no-show no backend Flask',
      data: String(error)
    })
  }
})
