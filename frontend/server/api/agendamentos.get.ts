import { listarAgenda } from '../features/agenda/service'
import { SERVER_MEDICO_ROLES } from '../utils/roles'

export default defineEventHandler(async (event) => {
  await requireRole(event, SERVER_MEDICO_ROLES)
  const query = getQuery(event)

  try {
    return await listarAgenda(event, query)
  } catch (error) {
    throwProxyError(error, 'Falha ao carregar agenda médica no backend Flask')
  }
})
