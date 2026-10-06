import { listarMedicosRecepcao } from '../../features/recepcao/service'
import { SERVER_RECEPCAO_ROLES } from '../../utils/roles'

export default defineEventHandler(async (event) => {
  await requireRole(event, SERVER_RECEPCAO_ROLES)
  try {
    return await listarMedicosRecepcao(event)
  } catch (error) {
    throwProxyError(error, 'Falha ao carregar médicos')
  }
})
