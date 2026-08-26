export default defineEventHandler(async (event) => {
  const id = getRouterParam(event, 'id')
  if (!id) throw createError({ statusCode: 400, statusMessage: 'id é obrigatório' })

  const body = await readBody(event)

  try {
    return await flaskFetch(event, `/usuarios/${id}`, {
      method: 'PUT',
      body
    })
  } catch (error) {
    throwProxyError(error, 'Erro ao atualizar usuário')
  }
})
