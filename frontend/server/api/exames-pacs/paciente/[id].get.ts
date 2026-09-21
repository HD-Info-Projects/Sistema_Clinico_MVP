import { listarExamesPacsPaciente, validarIdPacs } from '../../../features/pacs/service'

export default defineEventHandler(async (event) => {
  const id = validarIdPacs(Number(getRouterParam(event, 'id')), 'Paciente inválido')

  try {
    return await listarExamesPacsPaciente(event, id)
  } catch (error) {
    throwProxyError(error, 'Falha ao carregar resultados de exames no backend Flask')
  }
})
