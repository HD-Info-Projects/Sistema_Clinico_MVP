import type { H3Event } from 'h3'
import { flaskFetch } from '../../utils/flask'

export function listarDocumentosPorIds(event: H3Event, ids?: string) {
  const params = new URLSearchParams()
  if (ids) params.set('ids', ids)

  return flaskFetch(event, `/documentos-medicos${params.toString() ? `?${params.toString()}` : ''}`)
}

export function listarDocumentosPorAtendimento(event: H3Event, id?: string) {
  return flaskFetch(event, `/documentos-medicos/${id}`)
}

export function listarDocumentosPersonalizados(event: H3Event, id?: string) {
  return flaskFetch(event, `/documentos-medicos/${id}/personalizados`)
}

export function salvarDocumentoMedico(event: H3Event, id?: string, tipo?: string, body?: unknown) {
  return flaskFetch(event, `/documentos-medicos/${id}/${tipo}`, {
    method: 'PUT',
    body
  })
}

export function salvarDocumentoPersonalizado(
  event: H3Event,
  id?: string,
  body?: unknown,
  documentoId?: string
) {
  const suffix = documentoId ? `/${documentoId}` : ''
  return flaskFetch(event, `/documentos-medicos/${id}/personalizados${suffix}`, {
    method: documentoId ? 'PUT' : 'POST',
    body
  })
}

export function excluirDocumentoPersonalizado(event: H3Event, id?: string, documentoId?: string) {
  return flaskFetch(event, `/documentos-medicos/${id}/personalizados/${documentoId}`, {
    method: 'DELETE'
  })
}
