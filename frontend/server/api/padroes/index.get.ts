/* eslint-disable @typescript-eslint/no-explicit-any */
export default defineEventHandler(async (event) => {
  try {
    const [receitasRaw, examesRaw] = await Promise.all([
      flaskFetch<{ padroes_receitas: any[] }>(event, '/padrao_medico_receita/lista', { params: medicoAlvoParams(event) }),
      flaskFetch<{ padroes_exames: any[] }>(event, '/padrao_medico_exame/lista', { params: medicoAlvoParams(event) })
    ])

    const receitas = (receitasRaw.padroes_receitas || []).map(p => ({
      id: String(p.id),
      medicoId: Number(p.medico_id) || 0,
      nome: p.nome_modelo,
      tipo: 'receita' as const,
      medicamentos: (p.medicamentos || []).map((m: any) => ({
        id: String(m.id),
        nome: m.nome_medicamento,
        dosagem: m.dosagem,
        detalhes: m.detalhes || ''
      })),
      createdAt: p.created_at,
      updatedAt: p.updated_at
    }))

    const exames = (examesRaw.padroes_exames || []).map(p => ({
      id: String(p.id),
      medicoId: Number(p.medico_id) || 0,
      nome: p.nome_modelo,
      tipo: 'exame' as const,
      exames: (p.exames || []).map((e: any) => mapExameModelo(e)),
      createdAt: p.created_at,
      updatedAt: p.updated_at
    }))

    return [...receitas, ...exames]
  } catch (e) {
    throw createError({
      statusCode: 502,
      statusMessage: 'Falha ao conectar com o backend Flask',
      data: String(e)
    })
  }
})
