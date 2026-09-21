import { z } from 'zod'

export const ROLES_USUARIO = ['medico', 'recepcao', 'admin'] as const

export const medicoDadosSchema = z.object({
  spdata_id: z.coerce.number().int().positive(),
  crm: z.string().trim().max(20).optional(),
  crm_uf: z.string().trim().max(2).optional(),
  crm_atendimento_spdata: z.string().trim().max(50).optional(),
  rqe: z.string().trim().max(30).optional(),
  especialidade: z.string().trim().max(255).optional(),
  ativo: z.boolean().optional()
})

export const criarUsuarioSchema = z.object({
  nome_completo: z.string().trim().min(1).max(255),
  cnpj_cpf: z.string().trim().min(1).max(255),
  username: z.string().trim().regex(/^[a-z0-9._-]{3,30}$/, 'Usuário inválido'),
  email: z.email().max(254).optional(),
  senha: z.string().min(8).max(256),
  role: z.enum(ROLES_USUARIO),
  ativo: z.boolean().optional(),
  unidade_ids: z.array(z.number().int().positive()).optional(),
  medico: medicoDadosSchema.optional()
}).superRefine((data, ctx) => {
  if (data.role === 'medico' && (!data.medico || !data.medico.spdata_id)) {
    ctx.addIssue({
      code: 'custom',
      path: ['medico', 'spdata_id'],
      message: 'Informe o vínculo SPDATA do médico'
    })
  }
  if (data.role !== 'admin' && (!data.unidade_ids || data.unidade_ids.length === 0)) {
    ctx.addIssue({
      code: 'custom',
      path: ['unidade_ids'],
      message: 'Selecione ao menos uma unidade'
    })
  }
})

export const atualizarUsuarioSchema = z.object({
  nome_completo: z.string().trim().max(255).optional(),
  cnpj_cpf: z.string().trim().max(255).optional(),
  username: z.string().trim().regex(/^[a-z0-9._-]{3,30}$/, 'Usuário inválido').optional(),
  email: z.email().max(254).optional(),
  senha: z.string().min(8).max(256).optional(),
  role: z.enum(ROLES_USUARIO).optional(),
  ativo: z.boolean().optional(),
  unidade_ids: z.array(z.number().int().positive()).optional(),
  medico: medicoDadosSchema.optional()
}).superRefine((data, ctx) => {
  if (data.role === 'medico' && (!data.medico || !data.medico.spdata_id)) {
    ctx.addIssue({
      code: 'custom',
      path: ['medico', 'spdata_id'],
      message: 'Informe o vínculo SPDATA do médico'
    })
  }
  if ((data.role === 'medico' || data.role === 'recepcao') && data.unidade_ids && data.unidade_ids.length === 0) {
    ctx.addIssue({
      code: 'custom',
      path: ['unidade_ids'],
      message: 'Selecione ao menos uma unidade'
    })
  }
})

export type CriarUsuarioBody = z.infer<typeof criarUsuarioSchema>
export type AtualizarUsuarioBody = z.infer<typeof atualizarUsuarioSchema>
