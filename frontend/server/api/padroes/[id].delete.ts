import { deletarPadrao } from '../../features/clinico/service'

export default defineEventHandler(async (event) => {
  const id = getRouterParam(event, 'id')
  if (!id) throw createError({ statusCode: 400, statusMessage: 'id é obrigatório' })

  const query = getQuery(event)
  const tipo = query.tipo === 'exame' ? 'exame' : 'receita'

  return await deletarPadrao(event, id, tipo)
})
