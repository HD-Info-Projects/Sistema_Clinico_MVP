import { listarAuditoriasLgpd } from '../features/lgpd/service'
import { SERVER_LGPD_ROLES } from '../utils/roles'

export default defineEventHandler(async (event) => {
  await requireRole(event, SERVER_LGPD_ROLES)
  const query = getQuery(event)

  try {
    return await listarAuditoriasLgpd(event, query)
  } catch (error) {
    throwProxyError(error, 'Falha ao carregar auditoria LGPD')
  }
})
