import { listarPacientesFila } from '../features/pacientes/service'
import { SERVER_MEDICO_ROLES } from '../utils/roles'

export default defineEventHandler(async (event) => {
  await requireRole(event, SERVER_MEDICO_ROLES)
  try {
    return await listarPacientesFila(event)
  } catch (error) {
    throwProxyError(error, 'Falha ao carregar pacientes no backend Flask')
  }
})
