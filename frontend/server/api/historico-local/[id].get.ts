// Proxy para o endpoint do backend que retorna histórico do banco local
type FetchLikeError = {
  status?: number
  statusCode?: number
  response?: { status?: number }
}

function statusFetch(error: unknown): number | undefined {
  if (!error || typeof error !== 'object') return undefined
  const fetchError = error as FetchLikeError
  return fetchError.statusCode ?? fetchError.status ?? fetchError.response?.status
}

export default defineEventHandler(async (event) => {
  const id = getRouterParam(event, 'id')
  const query = getQuery(event)
  const params = new URLSearchParams()

  if (query.cpf) params.set('cpf', String(query.cpf))
  if (query.nome) params.set('nome', String(query.nome))
  if (query.spdataAtendimentoId) params.set('spdataAtendimentoId', String(query.spdataAtendimentoId))
  if (query.data) params.set('data', String(query.data))

  const qs = params.toString()
  try {
    return await flaskFetch(event, `/prontuario/historico-local/${id}${qs ? `?${qs}` : ''}`)
  } catch (error) {
    if (statusFetch(error) === 404) return []
    throw error
  }
})
