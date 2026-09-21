import { deletarPadraoDocumento } from '../../features/clinico/service'

export default defineEventHandler((event) => {
  const id = getRouterParam(event, 'id')
  if (!id) throw createError({ statusCode: 400, statusMessage: 'id é obrigatório' })
  return deletarPadraoDocumento(event, id)
})
