import { listarRetencaoExamesLgpd } from '../features/lgpd/service'

export default defineEventHandler(async (event) => {
  const query = getQuery(event)

  try {
    return await listarRetencaoExamesLgpd(event, query)
  } catch (error) {
    const fetchError = error as { status?: number, statusCode?: number, response?: { status?: number } }
    const status = fetchError.response?.status || fetchError.statusCode || fetchError.status || 502

    throw createError({
      statusCode: status,
      message: status === 401 ? 'Não autorizado' : status === 403 ? 'Acesso negado' : 'Falha ao carregar retenção de exames no backend Flask',
      data: String(error)
    })
  }
})
