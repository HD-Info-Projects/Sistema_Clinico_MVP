import { sincronizarCheckIn } from '../features/agenda/service'

export default defineEventHandler(async (event) => {
  const body = await readBody(event).catch(() => ({}))

  try {
    return await sincronizarCheckIn(event, body)
  } catch (error) {
    throwProxyError(error, 'Falha ao sincronizar check-in no backend Flask')
  }
})
