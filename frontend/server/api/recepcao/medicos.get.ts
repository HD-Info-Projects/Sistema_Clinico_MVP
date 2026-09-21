import { listarMedicosRecepcao } from '../../features/recepcao/service'

export default defineEventHandler(async (event) => {
  try {
    return await listarMedicosRecepcao(event)
  } catch (error) {
    throwProxyError(error, 'Falha ao carregar médicos')
  }
})
