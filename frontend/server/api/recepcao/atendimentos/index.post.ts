import { salvarAtendimentoRecepcao } from '../../../features/recepcao/service'
import { SERVER_RECEPCAO_ROLES } from '../../../utils/roles'

export default defineEventHandler(async (event) => {
  await requireRole(event, SERVER_RECEPCAO_ROLES)
  const body = await readBody(event)

  try {
    return await salvarAtendimentoRecepcao(event, body)
  } catch (error) {
    throwProxyError(error, 'Falha ao salvar atendimento no SPDATA')
  }
})
