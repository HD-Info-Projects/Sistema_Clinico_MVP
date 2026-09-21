import { salvarAtendimentoRecepcao } from '../../../features/recepcao/service'

export default defineEventHandler(async (event) => {
  const body = await readBody(event)

  try {
    return await salvarAtendimentoRecepcao(event, body)
  } catch (error) {
    throwProxyError(error, 'Falha ao salvar atendimento no SPDATA')
  }
})
