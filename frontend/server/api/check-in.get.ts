import { listarCheckIn } from '../features/agenda/service'

export default defineEventHandler(async (event) => {
  const query = getQuery(event)

  try {
    return await listarCheckIn(event, query)
  } catch (error) {
    throwProxyError(error, 'Falha ao conectar com o backend Flask')
  }
})
