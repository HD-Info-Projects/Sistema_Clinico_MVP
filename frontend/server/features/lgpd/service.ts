import type { H3Event } from 'h3'
import { flaskFetch } from '../../utils/flask'

function queryParams(query: Record<string, unknown>, keys: string[]) {
  const params = new URLSearchParams()
  for (const key of keys) {
    const value = query[key]
    if (value !== undefined && value !== null && String(value).trim()) {
      params.set(key, String(value))
    }
  }
  const qs = params.toString()
  return qs ? `?${qs}` : ''
}

export function listarAuditoriasLgpd(event: H3Event, query: Record<string, unknown>) {
  return flaskFetch(event, `/auditorias/${queryParams(query, ['dataIni', 'dataFim', 'acao', 'entidade', 'usuarioId', 'limit', 'offset'])}`)
}

export function listarRetencaoExamesLgpd(event: H3Event, query: Record<string, unknown>) {
  return flaskFetch(event, `/retencao-exames/${queryParams(query, ['dataIni', 'dataFim', 'unidadeId'])}`)
}
