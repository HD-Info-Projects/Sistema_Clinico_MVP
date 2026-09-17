import { z } from 'zod'

export const unidadeSchema = z.object({
  nome: z.string().trim().min(1).max(255),
  codigo_spdata_centro_custo: z.coerce.number().int().positive(),
  codigo_spdata_agenda: z.string().trim().min(1).max(50),
  endereco: z.string().trim().max(500).optional(),
  telefone: z.string().trim().max(50).optional(),
  ativa: z.boolean().optional()
})

export type UnidadeBody = z.infer<typeof unidadeSchema>
