import { criarPadraoAnamnese } from '../../features/clinico/service'
import { SERVER_MEDICO_ROLES } from '../../utils/roles'

export default defineEventHandler(async (event) => {
  await requireRole(event, SERVER_MEDICO_ROLES)
  const body = await readBody(event)
  return await criarPadraoAnamnese(event, body)
})
