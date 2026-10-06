// Proxy para o endpoint do backend que retorna histórico do banco local
import { buscarHistoricoLocal } from '../../features/pacientes/service'
import { SERVER_MEDICO_ROLES } from '../../utils/roles'

export default defineEventHandler(async (event) => {
  await requireRole(event, SERVER_MEDICO_ROLES)
  const id = getRouterParam(event, 'id')
  if (!id) {
    throw createError({
      statusCode: 400,
      statusMessage: 'id do paciente é obrigatório'
    })
  }
  const query = getQuery(event)

  return await buscarHistoricoLocal(event, id, query)
})
