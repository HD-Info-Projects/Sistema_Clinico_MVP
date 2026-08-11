export default defineEventHandler(async (event) => {
  try {
    const query = getQuery(event)
    const params = new URLSearchParams()

    const q = String(query.q || '').trim()
    const requestedLimit = Number(query.limit || 20)
    const requestedOffset = Number(query.offset || 0)
    const limit = Number.isFinite(requestedLimit) ? requestedLimit : 20
    const offset = Number.isFinite(requestedOffset) ? requestedOffset : 0

    if (q) params.set('q', q)
    params.set('limit', String(Math.min(Math.max(limit, 1), 50)))
    params.set('offset', String(Math.max(offset, 0)))

    const qs = params.toString()
    const raw = await flaskFetch<{ items: Record<string, unknown>[] }>(
      event,
      `/prontuario/doenca-cid?${qs}`,
      { activeClinica: false }
    )

    return raw.items.map((item: Record<string, unknown>) => ({
      cid: item.CID,
      nome: item.DOENCA
    }))
  } catch (error) {
    throwProxyError(error, 'Falha ao buscar CID no backend Flask')
  }
})
