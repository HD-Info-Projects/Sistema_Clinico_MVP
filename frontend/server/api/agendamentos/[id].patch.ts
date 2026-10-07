import { z } from 'zod'
import { atualizarStatusAtendimento } from '../../features/atendimentos/service'
import { SERVER_MEDICO_ROLES } from '../../utils/roles'

const atualizarStatusSchema = z.object({
  status: z.enum(['em-espera', 'em-atendimento', 'atendido', 'faltou', 'cancelado']),
  consulta: z.unknown().optional()
})

export default defineEventHandler(async (event) => {
  await requireRole(event, SERVER_MEDICO_ROLES)
  const id = Number(getRouterParam(event, 'id'))
  if (!Number.isInteger(id) || id <= 0) {
    throw createError({ statusCode: 400, statusMessage: 'id inválido' })
  }
  const body = await readBodyWithSchema(event, atualizarStatusSchema, 'Status inválido')

  try {
    const clinicaId = getActiveClinicaId(event)
    const result = await atualizarStatusAtendimento(event, id, body)

    broadcastSse({
      type: 'agendamento:status',
      data: {
        id: Number(result.id) || id,
        status: result.status || body.status,
        emEdicao: result.emEdicao ?? false,
        pacienteId: Number(result.pacienteId) || undefined
      }
    }, clinicaId)

    return result
  } catch (error) {
    throwProxyError(error, 'Falha ao atualizar status no backend Flask')
  }
})
