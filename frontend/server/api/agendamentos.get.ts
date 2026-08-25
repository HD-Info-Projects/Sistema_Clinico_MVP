export default defineEventHandler(async (event) => {
  const query = getQuery(event)
  const data = query.data ? String(query.data) : undefined
  const dataIni = query.dataIni ? String(query.dataIni) : undefined
  const dataFim = query.dataFim ? String(query.dataFim) : undefined
  const search = query.search ? String(query.search) : undefined
  const status = query.status ? String(query.status) : undefined
  const tipo = query.tipo ? String(query.tipo) : undefined

  const params = new URLSearchParams()
  if (data) params.set('data', data)
  if (dataIni) params.set('dataIni', dataIni)
  if (dataFim) params.set('dataFim', dataFim)
  if (search) params.set('search', search)
  if (status) params.set('status', status)
  if (tipo) params.set('tipo', tipo)

  try {
    return await flaskFetch(event, `/agenda-medica/${params.toString() ? `?${params.toString()}` : ''}`)
  } catch (error) {
    throwProxyError(error, 'Falha ao carregar agenda médica no backend Flask')
  }
})
