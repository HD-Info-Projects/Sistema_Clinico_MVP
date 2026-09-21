import { listarPacientesFila } from '../features/pacientes/service'

export default defineEventHandler(async (event) => {
  try {
    return await listarPacientesFila(event)
  } catch (error) {
    throwProxyError(error, 'Falha ao carregar pacientes no backend Flask')
  }
})
