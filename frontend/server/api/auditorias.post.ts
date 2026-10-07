import { z } from 'zod'

const eventoAuditoriaSchema = z.object({
  acao: z.enum([
    'ENTROU_MODULO',
    'SAIU_MODULO',
    'TROCOU_ACESSO',
    'MUDOU_UNIDADE',
    'ABRIU_PACIENTE',
    'CANCELOU_ACAO'
  ]),
  entidade: z.string().trim().min(1).max(100).default('modulo'),
  entidade_id: z.number().int().positive().optional(),
  entidadeId: z.number().int().positive().optional(),
  descricao: z.string().trim().max(1000).optional()
}).strict()

export default defineEventHandler(async (event) => {
  const body = await readBodyWithSchema(event, eventoAuditoriaSchema, 'Evento de auditoria inválido')

  try {
    return await flaskFetch(event, '/auditorias/eventos', {
      method: 'POST',
      body,
      activeClinica: false
    })
  } catch (error) {
    throwProxyError(error, 'Falha ao registrar evento de auditoria')
  }
})
