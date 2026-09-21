import { atualizarPadraoDocumento } from '../../features/clinico/service'

export default defineEventHandler(async (event) => {
  const id = getRouterParam(event, 'id')
  if (!id) throw createError({ statusCode: 400, statusMessage: 'id é obrigatório' })
  return atualizarPadraoDocumento(event, id, await readBody(event))
})
