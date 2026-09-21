import { buscarPacientesRecepcao } from '../../../features/recepcao/service'

export default defineEventHandler(async (event) => {
  const query = getQuery(event)

  try {
    return await buscarPacientesRecepcao(event, query)
  } catch (error) {
    throwProxyError(error, 'Falha ao buscar pacientes no SPDATA')
  }
})
