import { listarConveniosRecepcao } from '../../features/recepcao/service'

export default defineEventHandler(async (event) => {
  const query = getQuery(event)

  try {
    return await listarConveniosRecepcao(event, query)
  } catch (error) {
    throwProxyError(error, 'Falha ao carregar convênios')
  }
})
