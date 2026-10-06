import { salvarPacienteRecepcao } from '../../../features/recepcao/service'
import { SERVER_RECEPCAO_ROLES } from '../../../utils/roles'

export default defineEventHandler(async (event) => {
  await requireRole(event, SERVER_RECEPCAO_ROLES)
  const body = await readBody(event)

  try {
    return await salvarPacienteRecepcao(event, body)
  } catch (error) {
    throwProxyError(error, 'Falha ao salvar paciente no SPDATA')
  }
})
