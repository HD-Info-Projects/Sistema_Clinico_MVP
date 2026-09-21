import { obterPadrao } from '../../features/clinico/service'

export default defineEventHandler(async (event) => {
  const id = getRouterParam(event, 'id')
  if (!id) throw createError({ statusCode: 400, statusMessage: 'o id é obrigatorio ' })

  const query = getQuery(event)
  const tipo = query.tipo === 'exame' ? 'exame' : 'receita'

  return await obterPadrao(event, id, tipo)
})
