function normalizarCpf(valor: unknown): string | undefined {
  const texto = String(valor || '').trim()
  const semDecimal = texto.endsWith('.0') && [10, 11].includes(texto.slice(0, -2).replace(/\D/g, '').length)
    ? texto.slice(0, -2)
    : texto
  const digitos = semDecimal.replace(/\D/g, '')
  const cpf = digitos.length === 10 ? digitos.padStart(11, '0') : digitos

  if (cpf.length !== 11) return undefined
  if (new Set(cpf).size === 1) return undefined

  return cpf
}

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
  const cpf = normalizarCpf(query.cpf)
  const limit = Number(query.limit || 10)
  const offset = Number(query.offset || 0)

  if (cpf) params.set('cpf', cpf)
  if (query.nome) params.set('nome', String(query.nome))
  if (query.spdataAtendimentoId) params.set('spdataAtendimentoId', String(query.spdataAtendimentoId))
  params.set('limit', String(Number.isFinite(limit) ? Math.min(Math.max(limit, 1), 50) : 10))
  params.set('offset', String(Number.isFinite(offset) ? Math.max(offset, 0) : 0))

  const qs = params.toString()
  try {
    return await flaskFetch(event, `/prontuario/historico-paciente/${id}${qs ? `?${qs}` : ''}`)
  } catch (error) {
    if (statusFetch(error) === 404) {
      return { items: [], limit: Number.isFinite(limit) ? Math.min(Math.max(limit, 1), 50) : 10, offset: Number.isFinite(offset) ? Math.max(offset, 0) : 0, has_more: false }
    }
    throw error
  }
})
