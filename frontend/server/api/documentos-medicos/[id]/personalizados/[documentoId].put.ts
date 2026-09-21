import { salvarDocumentoPersonalizado } from '../../../../features/documentos/service'

export default defineEventHandler(async (event) => {
  const id = getRouterParam(event, 'id')
  const documentoId = getRouterParam(event, 'documentoId')
  const body = await readBody(event)
  return await salvarDocumentoPersonalizado(event, id, body, documentoId)
})
