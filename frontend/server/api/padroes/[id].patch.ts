import { atualizarPadrao } from '../../features/clinico/service'

export default defineEventHandler(async (event) => {
  const id = getRouterParam(event, 'id')
  if (!id) throw createError({ statusCode: 400, statusMessage: 'id é obrigatório' })

  const body = await readBody(event)
  return await atualizarPadrao(event, id, body)
})
