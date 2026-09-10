export default defineEventHandler(async (event) => {
  const body = await readBody(event)

  try {
    return await flaskFetch(event, '/recepcao/novo-atendimento', {
      method: 'POST',
      body,
      activeClinica: false
    })
  } catch (error) {
    throwProxyError(error, 'Falha ao salvar novo atendimento no SPDATA')
  }
})
