import { buscarSincronizacaoSpdata } from '../../../features/spdata-sync/service'

export default defineEventHandler(async (event) => {
  const id = Number(getRouterParam(event, 'id'))
  if (!Number.isInteger(id) || id <= 0) {
    throw createError({ statusCode: 400, statusMessage: 'ID inválido' })
  }

  try {
    return await buscarSincronizacaoSpdata(event, id)
  } catch (error) {
    throwProxyError(error, 'Erro ao consultar sincronização SPDATA')
  }
})
