export default defineEventHandler((event) => {
  const clinicaId = getActiveClinicaId(event)
  if (!clinicaId) throw createError({ statusCode: 400, statusMessage: 'clinicaId obrigatório' })

  return chamadoPublico(getChamadoAtivo(clinicaId))
})
