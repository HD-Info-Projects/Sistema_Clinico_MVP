import { buscarLaudoExamePacs, validarIdPacs } from '../../../features/pacs/service'

export default defineEventHandler(async (event) => {
  const id = validarIdPacs(Number(getRouterParam(event, 'id')), 'Exame inválido')

  try {
    return await buscarLaudoExamePacs(event, id)
  } catch (error) {
    throwProxyError(error, 'Falha ao carregar laudo do exame no backend Flask')
  }
})
