import { listarNoShow } from '../features/agenda/service'

export default defineEventHandler(async (event) => {
  const query = getQuery(event)

  try {
    return await listarNoShow(event, query)
  } catch (error) {
    throwProxyError(error, 'Falha ao carregar no-show no backend Flask')
  }
})
