import { listarUnidades } from '../../features/unidades/service'

export default defineEventHandler(async (event) => {
  try {
    return await listarUnidades(event)
  } catch (error) {
    throwProxyError(error, 'Erro ao carregar unidades')
  }
})
