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

export function salvarDocumentoMedico(event: H3Event, id?: string, tipo?: string, body?: unknown) {
  return flaskFetch(event, `/documentos-medicos/${id}/${tipo}`, {
    method: 'PUT',
    body
  })
}
