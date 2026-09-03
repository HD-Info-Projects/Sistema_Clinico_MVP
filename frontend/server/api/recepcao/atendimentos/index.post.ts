export default defineEventHandler(async (event) => {
  const body = await readBody(event)

  try {
    return await flaskFetch(event, '/recepcao/atendimentos', {
      method: 'POST',
      body
    })
  } catch (error) {
    throwProxyError(error, 'Falha ao salvar atendimento no SPDATA')
  }
})
