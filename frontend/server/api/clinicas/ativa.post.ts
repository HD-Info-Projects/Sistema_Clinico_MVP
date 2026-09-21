import { z } from 'zod'

const clinicaAtivaSchema = z.object({
  unidadeId: z.coerce.number().int().positive().optional(),
  clinicaId: z.coerce.number().int().positive().optional()
}).refine(body => body.unidadeId !== undefined || body.clinicaId !== undefined)

export default defineEventHandler(async (event) => {
  const rawUser = await getAuthenticatedUser(event)
  const clinicas = clinicasFromBackend(rawUser)
  const body = await readBodyWithSchema(event, clinicaAtivaSchema, 'Unidade inválida')
  const activeClinicaId = body.unidadeId ?? body.clinicaId!

  if (!clinicas.some(c => c.id === activeClinicaId)) {
    throw createError({ statusCode: 403, statusMessage: 'Acesso negado à unidade' })
  }

  setActiveClinicaIdCookie(event, activeClinicaId)

  return { activeClinicaId }
})
