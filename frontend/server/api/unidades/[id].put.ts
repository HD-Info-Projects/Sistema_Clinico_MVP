import { atualizarUnidade } from '../../features/unidades/service'

export default defineEventHandler(async (event) => {
  const id = getRouterParam(event, 'id')
  if (!id) throw createError({ statusCode: 400, statusMessage: 'id é obrigatório' })

  const body = await readBody(event)

  try {
    return await atualizarUnidade(event, id, body)
  } catch (error) {
    throwProxyError(error, 'Erro ao atualizar unidade')
  }
})
