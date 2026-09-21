import type { AuditoriaFiltros, AuditoriaResponse, RetencaoExamesFiltros, RetencaoExamesResponse } from '../types'

function queryParams(filtros: Record<string, unknown>) {
  const params = new URLSearchParams()
  for (const [key, value] of Object.entries(filtros)) {
    if (value !== undefined && value !== null && String(value).trim()) {
      params.set(key, String(value))
    }
  }
  const qs = params.toString()
  return qs ? `?${qs}` : ''
}

export function listarAuditorias(filtros: AuditoriaFiltros) {
  return $fetch<AuditoriaResponse>(`/api/auditorias${queryParams(filtros)}`)
}

export function listarRetencaoExames(filtros: RetencaoExamesFiltros) {
  return $fetch<RetencaoExamesResponse>(`/api/retencao-exames${queryParams(filtros)}`)
}
