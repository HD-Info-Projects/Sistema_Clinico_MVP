import { listarProcedimentosRecepcao } from '../../features/recepcao/service'
import { SERVER_RECEPCAO_ROLES } from '../../utils/roles'

export default defineEventHandler(async (event) => {
  await requireRole(event, SERVER_RECEPCAO_ROLES)
  const query = getQuery(event)

  try {
    return await listarProcedimentosRecepcao(event, query)
  } catch (error) {
    throwProxyError(error, 'Falha ao carregar procedimentos')
  }
})
