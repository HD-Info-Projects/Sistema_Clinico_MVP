import { salvarPacienteRecepcao } from '../../../features/recepcao/service'

export default defineEventHandler(async (event) => {
  const body = await readBody(event)

  try {
    return await salvarPacienteRecepcao(event, body)
  } catch (error) {
    throwProxyError(error, 'Falha ao salvar paciente no SPDATA')
  }
})
