import { listarDocumentosPorIds } from '../../features/documentos/service'

export default defineEventHandler(async (event) => {
  const query = getQuery(event)
  const ids = query.ids ? String(query.ids) : ''

  return await listarDocumentosPorIds(event, ids)
})
