/* eslint-disable @typescript-eslint/no-explicit-any */
export default defineEventHandler(async (event) => {
  const id = getRouterParam(event, 'id')
  if (!id) throw createError({ statusCode: 400, statusMessage: 'id é obrigatório' })

  const body = await readBody(event)
  const tipo = body.tipo === 'exame' ? 'exame' : 'receita'

  if (tipo === 'exame') {
    if (body.nome) {
      await flaskFetch<any>(event, `/padrao_medico_exame/editar/${id}`, {
        params: medicoAlvoParams(event),
        method: 'PUT',
        body: { nome_modelo: body.nome }
      })
    }

    if (body.exames) {
      const atual = await flaskFetch<any>(event, `/padrao_medico_exame/${id}`, { params: medicoAlvoParams(event) })

      for (const e of (atual.exames || [])) {
        await flaskFetch(event, `/padrao_medico_exame/deletar_exame/${e.id}`, {
          params: medicoAlvoParams(event),
          method: 'DELETE'
        })
      }

      for (const e of body.exames) {
        const examePayload = normalizarExamePayload(e)
        if (!examePayload) continue

        await flaskFetch(event, `/padrao_medico_exame/add_exame/${id}`, {
          params: medicoAlvoParams(event),
          method: 'POST',
          body: { nome_exame: examePayload.nome, exame_id: examePayload.exame_id }
        })
      }
    }

    const final = await flaskFetch<any>(event, `/padrao_medico_exame/${id}`, { params: medicoAlvoParams(event) })
    return {
      id: String(final.id),
      medicoId: Number(final.medico_id) || 0,
      nome: final.nome_modelo,
      tipo: 'exame' as const,
      exames: (final.exames || []).map((e: any) => mapExameModelo(e)),
      createdAt: final.created_at,
      updatedAt: final.updated_at
    }
  }

  if (body.nome) {
    await flaskFetch<any>(event, `/padrao_medico_receita/editar/${id}`, {
      params: medicoAlvoParams(event),
      method: 'PUT',
      body: { nome_modelo: body.nome }
    })
  }

  if (body.medicamentos) {
    const atual = await flaskFetch<any>(event, `/padrao_medico_receita/${id}`, { params: medicoAlvoParams(event) })

    for (const m of (atual.medicamentos || [])) {
      await flaskFetch(event, `/padrao_medico_receita/deletar_medicamento/${m.id}`, {
        params: medicoAlvoParams(event),
        method: 'DELETE'
      })
    }

    for (const m of body.medicamentos) {
      await flaskFetch(event, `/padrao_medico_receita/add_medicamento/${id}`, {
        params: medicoAlvoParams(event),
        method: 'POST',
        body: { nome_medicamento: m.nome, dosagem: m.dosagem, detalhes: m.detalhes || '' }
      })
    }
  }

  const final = await flaskFetch<any>(event, `/padrao_medico_receita/${id}`, { params: medicoAlvoParams(event) })
  return {
    id: String(final.id),
    medicoId: Number(final.medico_id) || 0,
    nome: final.nome_modelo,
    tipo: 'receita' as const,
    medicamentos: (final.medicamentos || []).map((m: any) => ({
      nome: m.nome_medicamento,
      dosagem: m.dosagem,
      detalhes: m.detalhes || ''
    })),
    createdAt: final.created_at,
    updatedAt: final.updated_at
  }
})
