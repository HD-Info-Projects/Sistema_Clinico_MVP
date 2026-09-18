import { desbloquearUsuario } from '../../../features/usuarios/service'

export default defineEventHandler(async (event) => {
  const id = getRouterParam(event, 'id')
  if (!id) throw createError({ statusCode: 400, statusMessage: 'id é obrigatório' })

  const idNum = Number(id)
  if (!Number.isInteger(idNum) || idNum <= 0) {
    throw createError({ statusCode: 400, statusMessage: 'id inválido' })
  }

  try {
    return await desbloquearUsuario(event, id)
  } catch (error) {
    throwProxyError(error, 'Erro ao desbloquear usuário')
  }
})
