import { criarUsuario } from '../../features/usuarios/service'
import { criarUsuarioSchema } from '../../features/usuarios/schema'

export default defineEventHandler(async (event) => {
  const body = await readBodyWithSchema(event, criarUsuarioSchema, 'Dados do usuário inválidos')

  try {
    return await criarUsuario(event, body)
  } catch (error) {
    throwProxyError(error, 'Erro ao criar usuário')
  }
})
