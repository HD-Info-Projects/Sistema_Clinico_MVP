import { iniciarSincronizacaoSpdata } from '../../../features/spdata-sync/service'

const targets = new Set(['TODOS', 'EXAMES', 'PROCEDIMENTOS'])

export default defineEventHandler(async (event) => {
  const body = await readBody<{ target?: string }>(event)
  const target = String(body?.target || 'TODOS').toUpperCase()
  if (!targets.has(target)) {
    throw createError({ statusCode: 400, statusMessage: 'Catálogo inválido' })
  }

  try {
    return await iniciarSincronizacaoSpdata(event, target)
  } catch (error) {
    throwProxyError(error, 'Erro ao iniciar sincronização SPDATA')
  }
})
