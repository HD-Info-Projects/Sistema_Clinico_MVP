import { buscarHistoricoSpdata } from '../../features/pacientes/service'
import { SERVER_MEDICO_ROLES } from '../../utils/roles'

export default defineEventHandler(async (event) => {
  await requireRole(event, SERVER_MEDICO_ROLES)
  const id = getRouterParam(event, 'id')
  if (!id) throw createError({ statusCode: 400, statusMessage: 'id é obrigatório' })
  const query = getQuery(event)

  return await buscarHistoricoSpdata(event, id, query)
})
