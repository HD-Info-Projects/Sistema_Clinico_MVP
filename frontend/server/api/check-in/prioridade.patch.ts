import { z } from 'zod'
import { atualizarPrioridadeCheckIn } from '../../features/agenda/service'
import { SERVER_RECEPCAO_ROLES } from '../../utils/roles'

const atualizarPrioridadeSchema = z.object({
  prioridadeOrigem: z.enum(['agenda', 'atendimento']),
  prioridadeSpdataId: z.number().int().positive(),
  prioridade: z.boolean()
}).strict()

export default defineEventHandler(async (event) => {
  await requireRole(event, SERVER_RECEPCAO_ROLES)
  const body = await readBodyWithSchema(event, atualizarPrioridadeSchema, 'Prioridade inválida')

  try {
    const clinicaId = getActiveClinicaId(event)
    const result = await atualizarPrioridadeCheckIn(event, body)

    broadcastSse({
      type: 'atendimento:prioridade',
      data: result
    }, clinicaId)

    return result
  } catch (error) {
    throwProxyError(error, 'Falha ao atualizar prioridade no backend Flask')
  }
})
