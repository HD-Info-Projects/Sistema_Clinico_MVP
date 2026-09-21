import { buscarExames } from '../../features/exames/service'

export default defineEventHandler(async (event) => {
  const query = getQuery(event)
  const q = query.q as string | undefined

  try {
    return await buscarExames(event, q)
  } catch (e) {
    throwProxyError(e, 'Falha ao buscar exames')
  }
})
