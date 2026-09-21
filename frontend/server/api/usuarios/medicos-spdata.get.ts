import { buscarMedicosSpdata } from '../../features/usuarios/service'

export default defineEventHandler(async (event) => {
  const query = getQuery(event)

  try {
    return await buscarMedicosSpdata(event, query)
  } catch (error) {
    throwProxyError(error, 'Erro ao buscar médicos no SPDATA')
  }
})
