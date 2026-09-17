import { registrarMotivoNoShow } from '../../../features/agenda/service'

export default defineEventHandler(async (event) => {
  const id = Number(getRouterParam(event, 'id'))
  if (!Number.isInteger(id) || id <= 0) {
    throw createError({ statusCode: 400, statusMessage: 'No-show inválido' })
  }

  const body = await readBody<{ motivo?: string }>(event)
  const motivo = String(body?.motivo ?? '').trim()
  const validMotivos = ['esquecimento', 'transporte', 'outros']

  if (!validMotivos.includes(motivo)) {
    throw createError({ statusCode: 400, statusMessage: 'Motivo da falta inválido' })
  }

  try {
    return await registrarMotivoNoShow(event, id, { motivo })
  } catch (error) {
    throwProxyError(error, 'Falha ao registrar motivo do no-show no backend Flask')
  }
})
