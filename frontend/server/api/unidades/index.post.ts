export default defineEventHandler(async (event) => {
  const body = await readBody(event)

  try {
    return await flaskFetch(event, '/unidades', {
      method: 'POST',
      body
    })
  } catch (error) {
    throwProxyError(error, 'Erro ao criar unidade')
  }
})
