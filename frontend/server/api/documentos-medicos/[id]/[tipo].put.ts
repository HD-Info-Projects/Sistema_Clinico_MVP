import { salvarDocumentoMedico } from '../../../features/documentos/service'

export default defineEventHandler(async (event) => {
  const id = getRouterParam(event, 'id')
  const tipo = getRouterParam(event, 'tipo')
  const body = await readBody(event)

  return await salvarDocumentoMedico(event, id, tipo, body)
})
