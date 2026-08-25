export default defineEventHandler(async (event) => {
  const query = getQuery(event)
  const params = new URLSearchParams()

  for (const key of ['dataIni', 'dataFim', 'medico', 'especialidade', 'convenio', 'status', 'q', 'page', 'pageSize', 'unidadeId']) {
    const value = query[key]
    if (value !== undefined && value !== null && String(value).trim()) {
      params.set(key, String(value))
    }
  }

  try {
    const qs = params.toString()
    return await flaskFetch(event, `/no_show/${qs ? `?${qs}` : ''}`)
  } catch (error) {
    const fetchError = error as { status?: number, statusCode?: number, response?: { status?: number } }
    const status = fetchError.response?.status || fetchError.statusCode || fetchError.status || 502

    throw createError({
      statusCode: status,
      message: status === 401 ? 'Não autorizado' : status === 403 ? 'Acesso negado' : 'Falha ao carregar no-show no backend Flask',
      data: String(error)
    })
  }
})
