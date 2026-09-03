export default defineEventHandler(async (event) => {
  try {
    return await flaskFetch(event, '/recepcao/medicos')
  } catch (error) {
    throwProxyError(error, 'Falha ao carregar médicos')
  }
})
