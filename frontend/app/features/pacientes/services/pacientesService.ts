import type {
  CidResultado,
  FiltrosCid,
  FiltrosHistoricoExterno,
  FiltrosHistoricoLocal,
  FiltrosPacientes,
  HistoricoLocalRecord,
  HistoricoResponse,
  Paciente,
  PacienteFila
} from '../types'

export type {
  CidResultado,
  FiltrosCid,
  FiltrosHistoricoExterno,
  FiltrosHistoricoLocal,
  FiltrosPacientes
}

function queryParams(filtros: Record<string, unknown>) {
  const params = new URLSearchParams()
  for (const [chave, valor] of Object.entries(filtros)) {
    if (valor !== undefined && valor !== null && String(valor).trim()) {
      params.set(chave, String(valor))
    }
  }
  const qs = params.toString()
  return qs ? `?${qs}` : ''
}

export function listarPacientes(filtros?: FiltrosPacientes) {
  return $fetch<Paciente[]>(`/api/pacientes${queryParams(filtros ?? {})}`)
}

export function listarPacientesFila(filtros?: FiltrosPacientes) {
  return $fetch<PacienteFila[]>(`/api/pacientes-fila${queryParams(filtros ?? {})}`)
}

export function buscarHistoricoLocal(pacienteId: number, filtros?: FiltrosHistoricoLocal) {
  return $fetch<HistoricoLocalRecord[]>(`/api/historico-local/${pacienteId}${queryParams(filtros ?? {})}`)
}

export function buscarHistoricoPaciente(pacienteId: number, filtros?: FiltrosHistoricoExterno) {
  return $fetch<HistoricoResponse>(`/api/historico-paciente/${pacienteId}${queryParams(filtros ?? {})}`)
}

export function buscarHistoricoSpdata(pacienteId: number, filtros?: FiltrosHistoricoExterno) {
  return $fetch<HistoricoResponse>(`/api/historico-spdata/${pacienteId}${queryParams(filtros ?? {})}`)
}

export function buscarCid(filtros?: FiltrosCid, signal?: AbortSignal) {
  return $fetch<CidResultado[]>(`/api/cid${queryParams(filtros ?? {})}`, { signal })
}
