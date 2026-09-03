export default defineEventHandler(async (event) => {
  const query = getQuery(event)
  const params = new URLSearchParams()

  for (const key of ['q', 'search', 'cpf', 'prontuario', 'id']) {
    const value = query[key]
    if (value !== undefined && value !== null && String(value).trim()) {
      params.set(key, String(value))
    }
  }

  try {
    const qs = params.toString()
    return await flaskFetch(event, `/recepcao/pacientes/buscar${qs ? `?${qs}` : ''}`)
  } catch (error) {
    throwProxyError(error, 'Falha ao buscar pacientes no SPDATA')
  }
})
