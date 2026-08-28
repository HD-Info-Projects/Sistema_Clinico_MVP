export default defineEventHandler(async (event) => {
  const body = await readBody<{ chamadoId?: number, clinicaId?: number }>(event)
  const clinicaId = getActiveClinicaId(event) ?? body?.clinicaId

  if (!clinicaId) throw createError({ statusCode: 400, statusMessage: 'clinicaId obrigatório' })

  const chamadoId = body?.chamadoId

  if (!chamadoId || !Number.isFinite(chamadoId) || chamadoId <= 0) {
    throw createError({ statusCode: 400, statusMessage: 'chamadoId inválido' })
  }

  const chamado = atualizarChamadoStatus(chamadoId, clinicaId, 'concluido')
  if (!chamado) {
    throw createError({ statusCode: 404, statusMessage: 'Chamado não encontrado' })
  }

  return chamadoPublico(chamado)
})
