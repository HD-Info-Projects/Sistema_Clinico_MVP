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
    throw createError({
      statusCode: 502,
      statusMessage: 'Falha ao registrar motivo do no-show no backend Flask',
      data: String(error)
    })
  }
})
