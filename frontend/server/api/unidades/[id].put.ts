import { atualizarUnidade } from '../../features/unidades/service'
import { unidadeSchema } from '../../features/unidades/schema'

export default defineEventHandler(async (event) => {
  const id = getRouterParam(event, 'id')
  if (!id) throw createError({ statusCode: 400, statusMessage: 'id é obrigatório' })

  const idNum = Number(id)
  if (!Number.isInteger(idNum) || idNum <= 0) {
    throw createError({ statusCode: 400, statusMessage: 'id inválido' })
  }

  const body = await readBodyWithSchema(event, unidadeSchema, 'Dados da unidade inválidos')

  try {
    return await atualizarUnidade(event, id, body)
  } catch (error) {
    throwProxyError(error, 'Erro ao atualizar unidade')
  }
})
