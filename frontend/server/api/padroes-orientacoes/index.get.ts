import { listarPadroesOrientacoes } from '../../features/clinico/service'

export default defineEventHandler(async (event) => {
  try {
    return await listarPadroesOrientacoes(event)
  } catch (e) {
    throw createError({
      statusCode: 502,
      statusMessage: 'Falha ao conectar com o backend Flask',
      data: String(e)
    })
  }
})
