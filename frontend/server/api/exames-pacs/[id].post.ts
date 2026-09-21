import { abrirViewerExamePacs, validarIdPacs } from '../../features/pacs/service'

export default defineEventHandler(async (event) => {
  const id = validarIdPacs(Number(getRouterParam(event, 'id')), 'Exame inválido')

  try {
    return await abrirViewerExamePacs(event, id)
  } catch (error) {
    throwProxyError(error, 'Falha ao abrir viewer de imagem no backend Flask')
  }
})
