/* eslint-disable @typescript-eslint/no-explicit-any */
import type { PadraoOrientacaoExame } from '~/types'

export default defineEventHandler(async (event): Promise<PadraoOrientacaoExame[]> => {
  try {
    const raw = await flaskFetch<{ padroes_orientacoes_exames: any[] }>(event, '/padrao_medico_orientacao_exame/lista', { params: medicoAlvoParams(event) })

    return (raw.padroes_orientacoes_exames || []).map(p => ({
      id: String(p.id),
      medicoId: Number(p.medico_id) || 0,
      nome: p.nome_modelo,
      conteudo: p.conteudo || '',
      createdAt: p.created_at,
      updatedAt: p.updated_at
    }))
  } catch (e) {
    throw createError({
      statusCode: 502,
      statusMessage: 'Falha ao conectar com o backend Flask',
      data: String(e)
    })
  }
})
