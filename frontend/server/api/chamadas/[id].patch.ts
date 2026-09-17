import { z } from 'zod'
import { atualizarChamadoStatus } from '../../features/chamadas/service'

const atualizarChamadoSchema = z.object({
  status: z.enum(['concluido', 'cancelado'])
})

export default defineEventHandler(async (event) => {
  const user = await requireRole(event, ['medico', 'recepcao'])
  const clinicaId = requireClinicaUsuario(event, user)
  const id = Number(getRouterParam(event, 'id'))

  if (!Number.isFinite(id) || id <= 0) {
    throw createError({ statusCode: 400, statusMessage: 'id inválido' })
  }

  const body = await readBodyWithSchema(event, atualizarChamadoSchema, 'Status inválido')

  const chamado = atualizarChamadoStatus(id, clinicaId, body.status)
  if (!chamado) {
    throw createError({ statusCode: 404, statusMessage: 'Chamado não encontrado' })
  }

  return chamado
})
