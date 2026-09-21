// Proxy para o endpoint do backend que retorna histórico do banco local
import { buscarHistoricoLocal } from '../../features/pacientes/service'

export default defineEventHandler(async (event) => {
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
