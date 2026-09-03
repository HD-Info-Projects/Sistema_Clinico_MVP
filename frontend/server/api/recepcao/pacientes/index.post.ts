export default defineEventHandler(async (event) => {
  const body = await readBody(event)

  try {
    return await flaskFetch(event, '/recepcao/pacientes', {
      method: 'POST',
      body
    })
  } catch (error) {
    throwProxyError(error, 'Falha ao salvar paciente no SPDATA')
  }
})
