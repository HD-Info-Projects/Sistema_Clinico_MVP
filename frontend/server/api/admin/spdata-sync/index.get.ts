import { listarSincronizacoesSpdata } from '../../../features/spdata-sync/service'

export default defineEventHandler(async (event) => {
  const query = getQuery(event)
  const limit = Math.min(Math.max(Number(query.limit) || 20, 1), 100)
  const offset = Math.max(Number(query.offset) || 0, 0)

  try {
    return await listarSincronizacoesSpdata(event, limit, offset)
  } catch (error) {
    throwProxyError(error, 'Erro ao carregar sincronizações SPDATA')
  }
})
