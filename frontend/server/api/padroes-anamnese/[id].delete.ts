import { deletarPadraoAnamnese } from '../../features/clinico/service'
import { SERVER_MEDICO_ROLES } from '../../utils/roles'

export default defineEventHandler(async (event) => {
  await requireRole(event, SERVER_MEDICO_ROLES)
  const id = getRouterParam(event, 'id')
  if (!id) throw createError({ statusCode: 400, statusMessage: 'id é obrigatório' })

  return await deletarPadraoAnamnese(event, id)
})
