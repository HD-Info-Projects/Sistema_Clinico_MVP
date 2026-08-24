export default defineEventHandler(async (event) => {
  const rawUser = await getAuthenticatedUser(event)
  const clinicas = clinicasFromBackend(rawUser)
  const body = await readBody<{ unidadeId?: unknown, clinicaId?: unknown }>(event) || {}
  const activeClinicaId = Number(body.unidadeId ?? body.clinicaId)

  if (!Number.isInteger(activeClinicaId) || activeClinicaId <= 0) {
    throw createError({ statusCode: 400, statusMessage: 'Unidade inválida' })
  }

  if (!clinicas.some(c => c.id === activeClinicaId)) {
    throw createError({ statusCode: 403, statusMessage: 'Acesso negado à unidade' })
  }

  setActiveClinicaIdCookie(event, activeClinicaId)

  return { activeClinicaId }
})
