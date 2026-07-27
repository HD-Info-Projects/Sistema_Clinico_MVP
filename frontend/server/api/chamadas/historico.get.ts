export default defineEventHandler((event) => {
  const query = getQuery(event)
  const limit = query.limit ? Number(query.limit) : 10

  return getHistoricoChamados(limit).map(chamadoPublico)
})
