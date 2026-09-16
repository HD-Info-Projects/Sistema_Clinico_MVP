import { salvarNovoAtendimentoRecepcao } from '../../features/recepcao/service'

export default defineEventHandler(async (event) => {
  const body = await readBody(event)

  try {
    return await salvarNovoAtendimentoRecepcao(event, body)
  } catch (error) {
    throwProxyError(error, 'Falha ao salvar novo atendimento no SPDATA')
  }
})
