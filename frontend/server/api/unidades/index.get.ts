export default defineEventHandler(async (event) => {
  try {
    return await flaskFetch(event, '/unidades')
  } catch (error) {
    throwProxyError(error, 'Erro ao carregar unidades')
  }
})
