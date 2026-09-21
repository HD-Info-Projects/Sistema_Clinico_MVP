import { listarAuditoriasLgpd } from '../features/lgpd/service'

export default defineEventHandler(async (event) => {
  const query = getQuery(event)

  try {
    return await listarAuditoriasLgpd(event, query)
  } catch (error) {
    throwProxyError(error, 'Falha ao carregar auditoria LGPD')
  }
})
