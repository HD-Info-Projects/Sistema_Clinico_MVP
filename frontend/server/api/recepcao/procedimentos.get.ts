import { listarProcedimentosRecepcao } from '../../features/recepcao/service'

export default defineEventHandler(async (event) => {
  const query = getQuery(event)

  try {
    return await listarProcedimentosRecepcao(event, query)
  } catch (error) {
    throwProxyError(error, 'Falha ao carregar procedimentos')
  }
})
