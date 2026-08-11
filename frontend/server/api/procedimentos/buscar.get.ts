export default defineEventHandler(async (event) => {
  const query = getQuery(event)
  const q = query.q as string | undefined

  const endpoint = q && q.length >= 2
    ? `/procedimentos/buscar?q=${encodeURIComponent(q)}`
    : '/procedimentos/buscar'

  try {
    return await flaskFetch(event, endpoint, { activeClinica: false })
  } catch (e) {
    throwProxyError(e, 'Falha ao buscar procedimentos')
  }
})
