import { buscarHistoricoSpdata } from '../../features/pacientes/service'

export default defineEventHandler(async (event) => {
  const id = getRouterParam(event, 'id')
  if (!id) throw createError({ statusCode: 400, statusMessage: 'id é obrigatório' })
  const query = getQuery(event)

  return await buscarHistoricoSpdata(event, id, query)
})
