import { buscarProcedimentos } from '../../features/procedimentos/service'

export default defineEventHandler(async (event) => {
  const query = getQuery(event)
  const q = query.q as string | undefined

  try {
    return await buscarProcedimentos(event, q)
  } catch (e) {
    throwProxyError(e, 'Falha ao buscar procedimentos')
  }
})
