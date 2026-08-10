export default defineEventHandler(async (event) => {
  const id = Number(getRouterParam(event, 'id'))
  const body = await readBody<{ status: string, consulta?: { anamnese?: string, diagnosticos?: { cid: string, descricao?: string, principal: boolean }[], medicamentos?: string, exames?: { nome: string, exame_id?: number | null, orientacao?: string | null }[], duracao?: number } }>(event)

  const validStatuses = ['em-espera', 'em-atendimento', 'atendido', 'faltou', 'cancelado']
  if (!body.status || !validStatuses.includes(body.status)) {
    throw createError({ statusCode: 400, message: 'Status inválido' })
  }

  try {
    const clinicaId = getActiveClinicaId(event)
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
    }, clinicaId)

    return result
  } catch (error) {
    throwProxyError(error, 'Falha ao atualizar status no backend Flask')
  }
})
