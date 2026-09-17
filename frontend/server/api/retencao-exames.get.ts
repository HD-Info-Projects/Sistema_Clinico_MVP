import { listarRetencaoExamesLgpd } from '../features/lgpd/service'

export default defineEventHandler(async (event) => {
  const query = getQuery(event)

  try {
    return await listarRetencaoExamesLgpd(event, query)
  } catch (error) {
    throwProxyError(error, 'Falha ao carregar retenção de exames no backend Flask')
  }
})
