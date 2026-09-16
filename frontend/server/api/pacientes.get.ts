import { listarPacientes } from '../features/pacientes/service'

export default defineEventHandler(async (event) => {
  const query = getQuery(event)

  try {
    return await listarPacientes(event, query)
  } catch (error) {
    throwProxyError(error, 'Falha ao carregar pacientes no backend Flask')
  }
})
