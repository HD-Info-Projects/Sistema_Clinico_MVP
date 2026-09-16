import { listarDocumentosPorAtendimento } from '../../features/documentos/service'

export default defineEventHandler(async (event) => {
  const id = getRouterParam(event, 'id')

  return await listarDocumentosPorAtendimento(event, id)
})
