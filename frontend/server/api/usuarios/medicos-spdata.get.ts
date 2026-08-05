export default defineEventHandler(async (event) => {
  const query = getQuery(event)
  const params = new URLSearchParams()

  for (const key of ['spdata_id', 'cpf', 'nome']) {
    if (query[key]) params.set(key, String(query[key]))
  }

  try {
    return await flaskFetch(event, `/usuarios/medicos-spdata${params.toString() ? `?${params.toString()}` : ''}`)
  } catch (error) {
    throwProxyError(error, 'Erro ao buscar médicos no SPDATA')
  }
})
