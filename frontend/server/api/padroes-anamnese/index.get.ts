import { listarPadroesAnamnese } from '../../features/clinico/service'
import { SERVER_MEDICO_ROLES } from '../../utils/roles'

export default defineEventHandler(async (event) => {
  await requireRole(event, SERVER_MEDICO_ROLES)
  try {
    return await listarPadroesAnamnese(event)
  } catch (e) {
    throw createError({
      statusCode: 502,
      statusMessage: 'Falha ao conectar com o backend Flask',
      data: String(e)
    })
  }
})
