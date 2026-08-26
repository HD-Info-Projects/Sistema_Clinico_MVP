/* eslint-disable @typescript-eslint/no-explicit-any */
import type { PadraoOrientacaoExame } from '~/types'

export default defineEventHandler(async (event): Promise<PadraoOrientacaoExame> => {
  const id = getRouterParam(event, 'id')
  if (!id) throw createError({ statusCode: 400, statusMessage: 'id é obrigatório' })

  const raw = await flaskFetch<any>(event, `/padrao_medico_orientacao_exame/${id}`, { params: medicoAlvoParams(event) })

  return {
    id: String(raw.id),
    medicoId: Number(raw.medico_id) || 0,
    nome: raw.nome_modelo,
    conteudo: raw.conteudo || '',
    createdAt: raw.created_at,
    updatedAt: raw.updated_at
  }
})
