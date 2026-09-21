import { excluirUnidade } from '../../features/unidades/service'

export default defineEventHandler(async (event) => {
  const id = getRouterParam(event, 'id')
  if (!id) throw createError({ statusCode: 400, statusMessage: 'id é obrigatório' })

  try {
    return await excluirUnidade(event, id)
  } catch (error) {
    throwProxyError(error, 'Erro ao inativar unidade')
  }
})
