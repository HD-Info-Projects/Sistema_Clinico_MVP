export default defineEventHandler((event) => {
  const query = getQuery(event)
  const clinicaId = getActiveClinicaId(event)
  if (!clinicaId) throw createError({ statusCode: 400, statusMessage: 'clinicaId obrigatório' })
  const limit = query.limit ? Number(query.limit) : 10

  return getHistoricoChamados(clinicaId, limit).map(chamadoPublico)
})
