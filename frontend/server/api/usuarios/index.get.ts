import { listarUsuarios } from '../../features/usuarios/service'

export default defineEventHandler(async (event) => {
  const query = getQuery(event)

  try {
    return await listarUsuarios(event, query.role ? String(query.role) : undefined)
  } catch (error) {
    throwProxyError(error, 'Erro ao carregar usuários')
  }
})
