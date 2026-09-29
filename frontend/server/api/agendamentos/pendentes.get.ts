import { listarAtendimentosPendentes } from '../../features/agenda/service'

export default defineEventHandler(async (event) => {
  const query = getQuery(event)

  try {
    return await listarAtendimentosPendentes(event, query)
  } catch (error) {
    throwProxyError(error, 'Falha ao carregar atendimentos pendentes no backend Flask')
  }
})
