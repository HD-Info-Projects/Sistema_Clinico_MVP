import { z } from 'zod'
import { criarChamado } from '../../features/chamadas/service'
import { SERVER_CHAMADAS_ROLES } from '../../utils/roles'

const criarChamadoSchema = z.object({
  pacienteId: z.number().int().positive(),
  pacienteNome: z.string().trim().min(1),
  localAtendimento: z.string().trim().min(1),
  medicoResponsavel: z.string().trim().optional()
})

export default defineEventHandler(async (event) => {
  const user = await requireRole(event, SERVER_CHAMADAS_ROLES)
  const clinicaId = requireClinicaUsuario(event, user)
  const body = await readBodyWithSchema(event, criarChamadoSchema, 'Dados da chamada inválidos')

  return criarChamado({
    clinicaId,
    pacienteId: body.pacienteId,
    pacienteNome: body.pacienteNome,
    localAtendimento: body.localAtendimento,
    medicoResponsavel: user.nome_completo || body.medicoResponsavel || 'Médico'
  })
})
