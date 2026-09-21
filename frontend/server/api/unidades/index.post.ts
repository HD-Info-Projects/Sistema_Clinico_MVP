import { criarUnidade } from '../../features/unidades/service'
import { unidadeSchema } from '../../features/unidades/schema'

export default defineEventHandler(async (event) => {
  const body = await readBodyWithSchema(event, unidadeSchema, 'Dados da unidade inválidos')

  try {
    return await criarUnidade(event, body)
  } catch (error) {
    throwProxyError(error, 'Erro ao criar unidade')
  }
})
