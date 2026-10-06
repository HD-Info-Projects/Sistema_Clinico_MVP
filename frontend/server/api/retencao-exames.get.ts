import { listarRetencaoExamesLgpd } from '../features/lgpd/service'
import { SERVER_COORD_RECEPCAO_ROLES } from '../utils/roles'

export default defineEventHandler(async (event) => {
  await requireRole(event, SERVER_COORD_RECEPCAO_ROLES)
  const query = getQuery(event)

  try {
    return await listarRetencaoExamesLgpd(event, query)
  } catch (error) {
    throwProxyError(error, 'Falha ao carregar retenção de exames no backend Flask')
  }
})
