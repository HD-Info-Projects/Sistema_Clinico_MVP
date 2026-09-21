import type {
  CidResultado,
  Padrao,
  PadraoAnamnese,
  PadraoDocumentoMedico,
  PadraoOrientacaoExame,
  PadraoPayload,
  PadraoTextoPayload
} from '../types'

function medicoParams(medicoId?: number) {
  return medicoId ? { medicoId } : undefined
}

export function listarPadroes(medicoId?: number) {
  return $fetch<Padrao[]>('/api/padroes', { params: medicoParams(medicoId) })
}

export function criarPadrao(data: PadraoPayload, medicoId?: number) {
  return $fetch<Padrao>('/api/padroes', {
    method: 'POST',
    body: data,
    params: medicoParams(medicoId)
  })
}

export function atualizarPadrao(id: string, data: Record<string, unknown>, medicoId?: number) {
  return $fetch<Padrao>(`/api/padroes/${id}`, {
    method: 'PATCH',
    body: data,
    params: medicoParams(medicoId)
  })
}

export function deletarPadrao(id: string, tipo?: string, medicoId?: number) {
  return $fetch(`/api/padroes/${id}`, {
    method: 'DELETE',
    params: { ...(tipo ? { tipo } : {}), ...(medicoId ? { medicoId } : {}) }
  })
}

export function listarPadroesAnamnese(medicoId?: number) {
  return $fetch<PadraoAnamnese[]>('/api/padroes-anamnese', { params: medicoParams(medicoId) })
}

export function criarPadraoAnamnese(data: PadraoTextoPayload, medicoId?: number) {
  return $fetch<PadraoAnamnese>('/api/padroes-anamnese', {
    method: 'POST',
    body: data,
    params: medicoParams(medicoId)
  })
}

export function atualizarPadraoAnamnese(id: string, data: Partial<PadraoTextoPayload>, medicoId?: number) {
  return $fetch<PadraoAnamnese>(`/api/padroes-anamnese/${id}`, {
    method: 'PATCH',
    body: data,
    params: medicoParams(medicoId)
  })
}

export function deletarPadraoAnamnese(id: string, medicoId?: number) {
  return $fetch(`/api/padroes-anamnese/${id}`, {
    method: 'DELETE',
    params: medicoParams(medicoId)
  })
}

export function listarPadroesOrientacoes(medicoId?: number) {
  return $fetch<PadraoOrientacaoExame[]>('/api/padroes-orientacoes', { params: medicoParams(medicoId) })
}

export function criarPadraoOrientacao(data: PadraoTextoPayload, medicoId?: number) {
  return $fetch<PadraoOrientacaoExame>('/api/padroes-orientacoes', {
    method: 'POST',
    body: data,
    params: medicoParams(medicoId)
  })
}

export function atualizarPadraoOrientacao(id: string, data: Partial<PadraoTextoPayload>, medicoId?: number) {
  return $fetch<PadraoOrientacaoExame>(`/api/padroes-orientacoes/${id}`, {
    method: 'PATCH',
    body: data,
    params: medicoParams(medicoId)
  })
}

export function deletarPadraoOrientacao(id: string, medicoId?: number) {
  return $fetch(`/api/padroes-orientacoes/${id}`, {
    method: 'DELETE',
    params: medicoParams(medicoId)
  })
}

export function listarPadroesDocumentos(medicoId?: number) {
  return $fetch<PadraoDocumentoMedico[]>('/api/padroes-documentos', { params: medicoParams(medicoId) })
}

export function criarPadraoDocumento(data: { nome: string, titulo: string, conteudo: string }, medicoId?: number) {
  return $fetch<PadraoDocumentoMedico>('/api/padroes-documentos', {
    method: 'POST',
    body: data,
    params: medicoParams(medicoId)
  })
}

export function atualizarPadraoDocumento(id: string, data: Partial<{ nome: string, titulo: string, conteudo: string }>, medicoId?: number) {
  return $fetch<PadraoDocumentoMedico>(`/api/padroes-documentos/${id}`, {
    method: 'PATCH',
    body: data,
    params: medicoParams(medicoId)
  })
}

export function deletarPadraoDocumento(id: string, medicoId?: number) {
  return $fetch(`/api/padroes-documentos/${id}`, {
    method: 'DELETE',
    params: medicoParams(medicoId)
  })
}

export function buscarCid(filtros: { q: string, limit?: number, offset?: number }, signal?: AbortSignal) {
  const params = new URLSearchParams()
  params.set('q', filtros.q)
  if (filtros.limit) params.set('limit', String(filtros.limit))
  if (filtros.offset) params.set('offset', String(filtros.offset))

  return $fetch<CidResultado[]>(`/api/cid?${params.toString()}`, { signal })
}
