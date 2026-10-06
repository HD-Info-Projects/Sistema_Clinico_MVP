import { buscarPacientesRecepcao } from '../../../features/recepcao/service'
import { SERVER_RECEPCAO_ROLES } from '../../../utils/roles'

export default defineEventHandler(async (event) => {
  await requireRole(event, SERVER_RECEPCAO_ROLES)
  const query = getQuery(event)

  try {
    return await buscarPacientesRecepcao(event, query)
  } catch (error) {
    throwProxyError(error, 'Falha ao buscar pacientes no SPDATA')
  }
})
