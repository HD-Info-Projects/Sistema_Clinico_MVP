export default defineEventHandler(async (event) => {
  const query = getQuery(event)
  const data = query.data ? String(query.data) : undefined
  const dataIni = query.dataIni ? String(query.dataIni) : undefined
  const dataFim = query.dataFim ? String(query.dataFim) : undefined
  const sincronizar = query.sincronizar ? String(query.sincronizar) : undefined

  const params = new URLSearchParams()
  if (data) params.set('data', data)
  if (dataIni) params.set('dataIni', dataIni)
  if (dataFim) params.set('dataFim', dataFim)
  if (sincronizar) params.set('sincronizar', sincronizar)

  try {
    return await flaskFetch(event, `/agenda-medica/marcadores${params.toString() ? `?${params.toString()}` : ''}`)
  } catch (error) {
    throwProxyError(error, 'Falha ao carregar marcadores da agenda médica no backend Flask')
  }
})
