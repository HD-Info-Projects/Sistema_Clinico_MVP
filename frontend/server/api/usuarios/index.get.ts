export default defineEventHandler(async (event) => {
  const query = getQuery(event)
  const params = new URLSearchParams()

  if (query.role) params.set('role', String(query.role))

  try {
    return await flaskFetch(event, `/usuarios${params.toString() ? `?${params.toString()}` : ''}`)
  } catch (error) {
    throwProxyError(error, 'Erro ao carregar usuários')
  }
})
