import { enviarPdfLaudoPacs, validarIdPacs } from '../../../../features/pacs/service'

export default defineEventHandler(async (event) => {
  const id = validarIdPacs(Number(getRouterParam(event, 'id')), 'Exame inválido')

  try {
    return await enviarPdfLaudoPacs(event, id)
  } catch (error) {
    throwProxyError(error, 'Falha ao carregar PDF do laudo no backend Flask')
  }
})
