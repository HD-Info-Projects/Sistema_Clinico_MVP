import { excluirUsuario } from '../../features/usuarios/service'

export default defineEventHandler(async (event) => {
  const id = getRouterParam(event, 'id')
  if (!id) throw createError({ statusCode: 400, statusMessage: 'id é obrigatório' })

  try {
    return await excluirUsuario(event, id)
  } catch (error) {
    throwProxyError(error, 'Erro ao inativar usuário')
  }
})
