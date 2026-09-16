import { listarAgenda } from '../features/agenda/service'

export default defineEventHandler(async (event) => {
  const query = getQuery(event)

  try {
    return await listarAgenda(event, query)
  } catch (error) {
    throwProxyError(error, 'Falha ao carregar agenda médica no backend Flask')
  }
})
