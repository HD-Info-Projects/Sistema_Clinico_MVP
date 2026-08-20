export default defineEventHandler(async (event) => {
  const user = await requireRole(event, ['medico', 'recepcao'])
  const clinicaId = requireClinicaUsuario(event, user)
  const body = await readBody<{ pacienteId: number, pacienteNome: string, localAtendimento: string, medicoResponsavel: string }>(event)

  if (!body.pacienteId || !body.pacienteNome || !body.localAtendimento) {
    throw createError({ statusCode: 400, statusMessage: 'Campos obrigatórios: pacienteId, pacienteNome, localAtendimento' })
  }

  return criarChamado({
    clinicaId,
    pacienteId: body.pacienteId,
    pacienteNome: body.pacienteNome,
    localAtendimento: body.localAtendimento,
    medicoResponsavel: user.nome_completo || body.medicoResponsavel || 'Médico'
  })
})
