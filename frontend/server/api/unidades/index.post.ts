import { criarUnidade } from '../../features/unidades/service'

export default defineEventHandler(async (event) => {
  const body = await readBody(event)

  try {
    return await criarUnidade(event, body)
  } catch (error) {
    throwProxyError(error, 'Erro ao criar unidade')
  }
})
