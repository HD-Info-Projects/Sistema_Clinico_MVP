import { buscarCid } from '../features/clinico/service'

export default defineEventHandler(async (event) => {
  const query = getQuery(event)

  try {
    return await buscarCid(event, query)
  } catch (error) {
    throwProxyError(error, 'Falha ao buscar CID no backend Flask')
  }
})
