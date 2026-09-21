import { listarDocumentosPersonalizados } from '../../../../features/documentos/service'

export default defineEventHandler(async (event) => {
  const id = getRouterParam(event, 'id')
  return await listarDocumentosPersonalizados(event, id)
})
