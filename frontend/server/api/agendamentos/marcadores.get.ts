import { listarMarcadoresAgenda } from '../../features/agenda/service'

export default defineEventHandler(async (event) => {
  const query = getQuery(event)

  try {
    return await listarMarcadoresAgenda(event, query)
  } catch (error) {
    throwProxyError(error, 'Falha ao carregar marcadores da agenda médica no backend Flask')
  }
})
