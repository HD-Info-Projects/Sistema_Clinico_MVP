import { criarUsuario } from '../../features/usuarios/service'

export default defineEventHandler(async (event) => {
  const body = await readBody(event)

  try {
    return await criarUsuario(event, body)
  } catch (error) {
    throwProxyError(error, 'Erro ao criar usuário')
  }
})
