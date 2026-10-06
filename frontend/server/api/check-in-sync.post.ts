import { sincronizarCheckIn } from '../features/agenda/service'
import { SERVER_RECEPCAO_ROLES } from '../utils/roles'

export default defineEventHandler(async (event) => {
  await requireRole(event, SERVER_RECEPCAO_ROLES)
  const body = await readBody(event).catch(() => ({}))

  try {
    return await sincronizarCheckIn(event, body)
  } catch (error) {
    throwProxyError(error, 'Falha ao sincronizar check-in no backend Flask')
  }
})
