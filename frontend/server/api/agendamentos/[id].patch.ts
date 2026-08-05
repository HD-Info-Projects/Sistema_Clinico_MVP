export default defineEventHandler(async (event) => {
  const id = Number(getRouterParam(event, 'id'))
  const body = await readBody<{ status: string, consulta?: { anamnese?: string, diagnosticos?: { cid: string, descricao?: string, principal: boolean }[], medicamentos?: string, exames?: { nome: string, exame_id?: number | null, orientacao?: string | null }[], duracao?: number } }>(event)

  const validStatuses = ['em-espera', 'em-atendimento', 'atendido', 'faltou', 'cancelado']
  if (!body.status || !validStatuses.includes(body.status)) {
    throw createError({ statusCode: 400, statusMessage: 'Status inválido' })
  }

  try {
    const result = await flaskFetch<{ id?: number, status?: string, pacienteId?: number }>(event, `/agenda-medica/${id}/status`, {
      method: 'PATCH',
      body
    })

    broadcastSse({
      type: 'agendamento:status',
      data: {
        id: Number(result.id) || id,
        status: result.status || body.status,
        pacienteId: Number(result.pacienteId) || undefined
      }
    })

    return result
  } catch (error) {
    throw createError({
      statusCode: 502,
      statusMessage: 'Falha ao atualizar status no backend Flask',
      data: String(error)
    })
  }
})
