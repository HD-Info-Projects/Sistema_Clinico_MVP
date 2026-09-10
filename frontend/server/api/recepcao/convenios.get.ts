export default defineEventHandler(async (event) => {
  const query = getQuery(event)
  const params = new URLSearchParams()
  if (query.q) params.set('q', String(query.q))

  try {
    const qs = params.toString()
    return await flaskFetch(event, `/recepcao/convenios${qs ? `?${qs}` : ''}`)
  } catch (error) {
    throwProxyError(error, 'Falha ao carregar convênios')
  }
})
