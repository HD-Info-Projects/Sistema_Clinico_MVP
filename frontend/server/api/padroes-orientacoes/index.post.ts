/* eslint-disable @typescript-eslint/no-explicit-any */
import type { PadraoOrientacaoExame } from '~/types'

export default defineEventHandler(async (event): Promise<PadraoOrientacaoExame> => {
  const body = await readBody(event)
  if (!body.nome || !body.conteudo) {
    throw createError({ statusCode: 400, statusMessage: 'nome e conteudo são obrigatórios' })
  }

  const raw = await flaskFetch<any>(event, '/padrao_medico_orientacao_exame/criar', {
    params: medicoAlvoParams(event),
    method: 'POST',
    body: { nome_modelo: body.nome, conteudo: body.conteudo }
  })

  return {
    id: String(raw.id),
    medicoId: Number(raw.medico_id) || 0,
    nome: raw.nome_modelo,
    conteudo: raw.conteudo || '',
    createdAt: raw.created_at,
    updatedAt: raw.updated_at
  }
})
