import { z } from 'zod'
import { atualizarStatusExame } from '../../../features/agenda/service'
import { SERVER_ASSISTENTE_ROLES } from '../../../utils/roles'

const atualizarStatusExameSchema = z.object({
  status: z.enum(['atendido', 'faltou'])
})

export default defineEventHandler(async (event) => {
  await requireRole(event, SERVER_ASSISTENTE_ROLES)
  const id = Number(getRouterParam(event, 'id'))
  if (!Number.isInteger(id) || id <= 0) {
    throw createError({ statusCode: 400, statusMessage: 'id inválido' })
  }
  const body = await readBodyWithSchema(event, atualizarStatusExameSchema, 'Status inválido')

  try {
    const clinicaId = getActiveClinicaId(event)
    const result = await atualizarStatusExame(event, id, body)

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
    throwProxyError(error, 'Falha ao atualizar agenda do assistente no backend Flask')
  }
})
