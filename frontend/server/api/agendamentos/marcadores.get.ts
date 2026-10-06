import { listarMarcadoresAgenda } from '../../features/agenda/service'
import { SERVER_MEDICO_ROLES } from '../../utils/roles'

export default defineEventHandler(async (event) => {
  await requireRole(event, SERVER_MEDICO_ROLES)
  const query = getQuery(event)

  try {
    return await listarMarcadoresAgenda(event, query)
  } catch (error) {
    throwProxyError(error, 'Falha ao carregar marcadores da agenda médica no backend Flask')
  }
})
