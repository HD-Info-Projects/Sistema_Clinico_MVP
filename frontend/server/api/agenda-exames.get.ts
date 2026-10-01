import { listarAgendaExames } from '../features/agenda/service'
import { SERVER_ASSISTENTE_ROLES } from '../utils/roles'

export default defineEventHandler(async (event) => {
  await requireRole(event, SERVER_ASSISTENTE_ROLES)
  const query = getQuery(event)

  try {
    return await listarAgendaExames(event, query)
  } catch (error) {
    throwProxyError(error, 'Falha ao carregar agenda de exames no backend Flask')
  }
})
