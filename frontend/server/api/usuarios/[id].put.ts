import { atualizarUsuario } from '../../features/usuarios/service'
import { atualizarUsuarioSchema } from '../../features/usuarios/schema'

export default defineEventHandler(async (event) => {
  const id = getRouterParam(event, 'id')
  if (!id) throw createError({ statusCode: 400, statusMessage: 'id é obrigatório' })

  const idNum = Number(id)
  if (!Number.isInteger(idNum) || idNum <= 0) {
    throw createError({ statusCode: 400, statusMessage: 'id inválido' })
  }

  const body = await readBodyWithSchema(event, atualizarUsuarioSchema, 'Dados do usuário inválidos')

  try {
    return await atualizarUsuario(event, id, body)
  } catch (error) {
    throwProxyError(error, 'Erro ao atualizar usuário')
  }
})
