export default defineEventHandler(async (event) => {
  const query = getQuery(event)
  const q = query.q as string | undefined

  const endpoint = q && q.length >= 2
    ? `/exames/buscar?q=${encodeURIComponent(q)}`
    : '/exames'

  try {
    return await flaskFetch(event, endpoint, { activeClinica: false })
  } catch (e) {
    throwProxyError(e, 'Falha ao buscar exames')
  }
})
