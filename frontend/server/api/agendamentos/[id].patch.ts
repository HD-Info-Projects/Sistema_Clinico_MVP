import { z } from 'zod'
import { atualizarStatusAtendimento } from '../../features/atendimentos/service'

const atualizarStatusSchema = z.object({
  status: z.enum(['em-espera', 'em-atendimento', 'atendido', 'faltou', 'cancelado']),
  consulta: z.unknown().optional()
})

export default defineEventHandler(async (event) => {
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
        pacienteId: Number(result.pacienteId) || undefined
      }
    }, clinicaId)

    return result
  } catch (error) {
    throwProxyError(error, 'Falha ao atualizar status no backend Flask')
  }
})
