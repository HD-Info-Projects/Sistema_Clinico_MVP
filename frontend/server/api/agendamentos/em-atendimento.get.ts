import { verificarAtendimentoEmAndamento } from '../../features/agenda/service'

export default defineEventHandler(async (event) => {
  const query = getQuery(event)

  try {
    return await verificarAtendimentoEmAndamento(event, query)
  } catch (error) {
    throwProxyError(error, 'Falha ao verificar atendimento em andamento no backend Flask')
  }
})
