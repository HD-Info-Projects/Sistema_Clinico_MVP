/* eslint-disable @typescript-eslint/no-explicit-any */
import type { H3Event } from 'h3'
import type { PadraoAnamnese, PadraoDocumentoMedico, PadraoOrientacaoExame } from '~/types'
import { flaskFetch, medicoAlvoParams } from '../../utils/flask'
import { mapExameModelo, normalizarExamePayload } from '../../utils/exames'

type PadraoTipo = 'receita' | 'exame'

function tipoPadrao(valor: unknown): PadraoTipo {
  return valor === 'exame' ? 'exame' : 'receita'
}

function mapReceita(raw: any) {
  return {
    id: String(raw.id),
    medicoId: Number(raw.medico_id) || 0,
    nome: raw.nome_modelo,
    tipo: 'receita' as const,
    medicamentos: (raw.medicamentos || []).map((m: any) => ({
      id: String(m.id),
      nome: m.nome_medicamento,
      dosagem: m.dosagem,
      detalhes: m.detalhes || ''
    })),
    createdAt: raw.created_at,
    updatedAt: raw.updated_at
  }
}

function mapExame(raw: any) {
  return {
    id: String(raw.id),
    medicoId: Number(raw.medico_id) || 0,
    nome: raw.nome_modelo,
    tipo: 'exame' as const,
    exames: (raw.exames || []).map((e: any) => mapExameModelo(e)),
    createdAt: raw.created_at,
    updatedAt: raw.updated_at
  }
}

function mapAnamnese(raw: any): PadraoAnamnese {
  return {
    id: String(raw.id),
    medicoId: Number(raw.medico_id) || 0,
    nome: raw.nome_modelo,
    conteudo: raw.conteudo || '',
    createdAt: raw.created_at,
    updatedAt: raw.updated_at
  }
}

function mapOrientacao(raw: any): PadraoOrientacaoExame {
  return {
    id: String(raw.id),
    medicoId: Number(raw.medico_id) || 0,
    nome: raw.nome_modelo,
    conteudo: raw.conteudo || '',
    createdAt: raw.created_at,
    updatedAt: raw.updated_at
  }
}

function mapDocumento(raw: any): PadraoDocumentoMedico {
  return {
    id: String(raw.id),
    medicoId: Number(raw.medico_id) || 0,
    nome: raw.nome_modelo,
    titulo: raw.titulo_documento,
    conteudo: raw.conteudo || '',
    createdAt: raw.created_at,
    updatedAt: raw.updated_at
  }
}

export async function listarPadroes(event: H3Event) {
  const [receitasRaw, examesRaw] = await Promise.all([
    flaskFetch<{ padroes_receitas: any[] }>(event, '/padrao_medico_receita/lista', { params: medicoAlvoParams(event) }),
    flaskFetch<{ padroes_exames: any[] }>(event, '/padrao_medico_exame/lista', { params: medicoAlvoParams(event) })
  ])

  return [
    ...(receitasRaw.padroes_receitas || []).map(mapReceita),
    ...(examesRaw.padroes_exames || []).map(mapExame)
  ]
}

export async function obterPadrao(event: H3Event, id: string, tipo: PadraoTipo) {
  if (tipo === 'exame') {
    const raw = await flaskFetch<any>(event, `/padrao_medico_exame/${id}`, { params: medicoAlvoParams(event) })
    return mapExame(raw)
  }

  const raw = await flaskFetch<any>(event, `/padrao_medico_receita/${id}`, { params: medicoAlvoParams(event) })
  return mapReceita(raw)
}

export async function criarPadrao(event: H3Event, body: any) {
  if (!body.nome || !body.tipo) {
    throw createError({ statusCode: 400, statusMessage: 'nome e tipo são obrigatórios' })
  }

  if (body.tipo === 'exame') {
    const template = await flaskFetch<any>(event, '/padrao_medico_exame/criar', {
      params: medicoAlvoParams(event),
      method: 'POST',
      body: { nome_modelo: body.nome }
    })

    const examesCriados: { nome: string, exameId: number | null }[] = []
    for (const e of (body.exames || [])) {
      const examePayload = normalizarExamePayload(e)
      if (!examePayload) continue

      const exame = await flaskFetch<any>(event, `/padrao_medico_exame/add_exame/${template.id}`, {
        params: medicoAlvoParams(event),
        method: 'POST',
        body: { nome_exame: examePayload.nome, exame_id: examePayload.exame_id }
      })
      examesCriados.push(mapExameModelo(exame))
    }

    return {
      id: String(template.id),
      medicoId: Number(template.medico_id),
      nome: template.nome_modelo,
      tipo: 'exame' as const,
      exames: examesCriados,
      createdAt: template.created_at,
      updatedAt: template.updated_at
    }
  }

  const template = await flaskFetch<any>(event, '/padrao_medico_receita/criar', {
    params: medicoAlvoParams(event),
    method: 'POST',
    body: { nome_modelo: body.nome }
  })

  const medicamentosCriados: any[] = []
  for (const m of (body.medicamentos || [])) {
    const med = await flaskFetch<any>(event, `/padrao_medico_receita/add_medicamento/${template.id}`, {
      params: medicoAlvoParams(event),
      method: 'POST',
      body: { nome_medicamento: m.nome, dosagem: m.dosagem, detalhes: m.detalhes || '' }
    })
    medicamentosCriados.push(med)
  }

  return {
    id: String(template.id),
    medicoId: Number(template.medico_id),
    nome: template.nome_modelo,
    tipo: 'receita' as const,
    medicamentos: medicamentosCriados.map((m: any) => ({
      nome: m.nome_medicamento,
      dosagem: m.dosagem,
      detalhes: m.detalhes || ''
    })),
    createdAt: template.created_at,
    updatedAt: template.updated_at
  }
}

export async function atualizarPadrao(event: H3Event, id: string, body: any) {
  const tipo = tipoPadrao(body.tipo)

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

    return obterPadrao(event, id, 'exame')
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

  return obterPadrao(event, id, 'receita')
}

export async function deletarPadrao(event: H3Event, id: string, tipo: PadraoTipo) {
  if (tipo === 'exame') {
    await flaskFetch(event, `/padrao_medico_exame/deletar/${id}`, { method: 'DELETE', params: medicoAlvoParams(event) })
  } else {
    await flaskFetch(event, `/padrao_medico_receita/deletar/${id}`, { method: 'DELETE', params: medicoAlvoParams(event) })
  }

  return { success: true }
}

export async function listarPadroesAnamnese(event: H3Event): Promise<PadraoAnamnese[]> {
  const raw = await flaskFetch<{ padroes_anamnese: any[] }>(event, '/padrao_medico_anamnese/lista', { params: medicoAlvoParams(event) })
  return (raw.padroes_anamnese || []).map(mapAnamnese)
}

export async function obterPadraoAnamnese(event: H3Event, id: string): Promise<PadraoAnamnese> {
  const raw = await flaskFetch<any>(event, `/padrao_medico_anamnese/${id}`, { params: medicoAlvoParams(event) })
  return mapAnamnese(raw)
}

export async function criarPadraoAnamnese(event: H3Event, body: any): Promise<PadraoAnamnese> {
  if (!body.nome || !body.conteudo) {
    throw createError({ statusCode: 400, statusMessage: 'nome e conteudo são obrigatórios' })
  }

  const raw = await flaskFetch<any>(event, '/padrao_medico_anamnese/criar', {
    params: medicoAlvoParams(event),
    method: 'POST',
    body: { nome_modelo: body.nome, conteudo: body.conteudo }
  })

  return mapAnamnese(raw)
}

export async function atualizarPadraoAnamnese(event: H3Event, id: string, body: any): Promise<PadraoAnamnese> {
  const raw = await flaskFetch<any>(event, `/padrao_medico_anamnese/editar/${id}`, {
    params: medicoAlvoParams(event),
    method: 'PUT',
    body: { nome_modelo: body.nome, conteudo: body.conteudo }
  })

  return mapAnamnese(raw)
}

export async function deletarPadraoAnamnese(event: H3Event, id: string) {
  await flaskFetch(event, `/padrao_medico_anamnese/deletar/${id}`, {
    params: medicoAlvoParams(event),
    method: 'DELETE'
  })

  return { success: true }
}

export async function listarPadroesOrientacoes(event: H3Event): Promise<PadraoOrientacaoExame[]> {
  const raw = await flaskFetch<{ padroes_orientacoes_exames: any[] }>(event, '/padrao_medico_orientacao_exame/lista', { params: medicoAlvoParams(event) })
  return (raw.padroes_orientacoes_exames || []).map(mapOrientacao)
}

export async function obterPadraoOrientacao(event: H3Event, id: string): Promise<PadraoOrientacaoExame> {
  const raw = await flaskFetch<any>(event, `/padrao_medico_orientacao_exame/${id}`, { params: medicoAlvoParams(event) })
  return mapOrientacao(raw)
}

export async function criarPadraoOrientacao(event: H3Event, body: any): Promise<PadraoOrientacaoExame> {
  if (!body.nome || !body.conteudo) {
    throw createError({ statusCode: 400, statusMessage: 'nome e conteudo são obrigatórios' })
  }

  const raw = await flaskFetch<any>(event, '/padrao_medico_orientacao_exame/criar', {
    params: medicoAlvoParams(event),
    method: 'POST',
    body: { nome_modelo: body.nome, conteudo: body.conteudo }
  })

  return mapOrientacao(raw)
}

export async function atualizarPadraoOrientacao(event: H3Event, id: string, body: any): Promise<PadraoOrientacaoExame> {
  const raw = await flaskFetch<any>(event, `/padrao_medico_orientacao_exame/editar/${id}`, {
    params: medicoAlvoParams(event),
    method: 'PUT',
    body: { nome_modelo: body.nome, conteudo: body.conteudo }
  })

  return mapOrientacao(raw)
}

export async function deletarPadraoOrientacao(event: H3Event, id: string) {
  await flaskFetch(event, `/padrao_medico_orientacao_exame/deletar/${id}`, {
    params: medicoAlvoParams(event),
    method: 'DELETE'
  })

  return { ok: true }
}

export async function listarPadroesDocumentos(event: H3Event): Promise<PadraoDocumentoMedico[]> {
  const raw = await flaskFetch<{ padroes_documentos: any[] }>(event, '/padrao_medico_documento/lista', { params: medicoAlvoParams(event) })
  return (raw.padroes_documentos || []).map(mapDocumento)
}

export async function obterPadraoDocumento(event: H3Event, id: string): Promise<PadraoDocumentoMedico> {
  const raw = await flaskFetch<any>(event, `/padrao_medico_documento/${id}`, { params: medicoAlvoParams(event) })
  return mapDocumento(raw)
}

export async function criarPadraoDocumento(event: H3Event, body: any): Promise<PadraoDocumentoMedico> {
  if (!body?.nome || !body?.titulo || !body?.conteudo) {
    throw createError({ statusCode: 400, statusMessage: 'nome, titulo e conteudo são obrigatórios' })
  }
  const raw = await flaskFetch<any>(event, '/padrao_medico_documento/criar', {
    params: medicoAlvoParams(event),
    method: 'POST',
    body: {
      nome_modelo: body.nome,
      titulo_documento: body.titulo,
      conteudo: body.conteudo
    }
  })
  return mapDocumento(raw)
}

export async function atualizarPadraoDocumento(event: H3Event, id: string, body: any): Promise<PadraoDocumentoMedico> {
  const raw = await flaskFetch<any>(event, `/padrao_medico_documento/editar/${id}`, {
    params: medicoAlvoParams(event),
    method: 'PATCH',
    body: {
      ...(body.nome !== undefined ? { nome_modelo: body.nome } : {}),
      ...(body.titulo !== undefined ? { titulo_documento: body.titulo } : {}),
      ...(body.conteudo !== undefined ? { conteudo: body.conteudo } : {})
    }
  })
  return mapDocumento(raw)
}

export async function deletarPadraoDocumento(event: H3Event, id: string) {
  await flaskFetch(event, `/padrao_medico_documento/deletar/${id}`, {
    params: medicoAlvoParams(event),
    method: 'DELETE'
  })
  return { ok: true }
}

export async function buscarCid(event: H3Event, query: Record<string, unknown>) {
  const params = new URLSearchParams()

  const q = String(query.q || '').trim()
  const requestedLimit = Number(query.limit || 20)
  const requestedOffset = Number(query.offset || 0)
  const limit = Number.isFinite(requestedLimit) ? requestedLimit : 20
  const offset = Number.isFinite(requestedOffset) ? requestedOffset : 0

  if (q) params.set('q', q)
  params.set('limit', String(Math.min(Math.max(limit, 1), 50)))
  params.set('offset', String(Math.max(offset, 0)))

  const qs = params.toString()
  const raw = await flaskFetch<{ items: Record<string, unknown>[] }>(
    event,
    `/prontuario/doenca-cid?${qs}`,
    { activeClinica: false }
  )

  return raw.items.map((item: Record<string, unknown>) => ({
    cid: item.CID,
    nome: item.DOENCA
  }))
}
