import { excluirDocumentoPersonalizado } from '../../../../features/documentos/service'

export default defineEventHandler(async (event) => {
  const id = getRouterParam(event, 'id')
  const documentoId = getRouterParam(event, 'documentoId')
  return await excluirDocumentoPersonalizado(event, id, documentoId)
})
