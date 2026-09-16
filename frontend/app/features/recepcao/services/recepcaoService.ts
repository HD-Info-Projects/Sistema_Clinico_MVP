import type {
  BuscarPacientesRecepcaoResponse,
  ListarConveniosRecepcaoResponse,
  ListarMedicosRecepcaoResponse,
  ListarProcedimentosRecepcaoResponse,
  SalvarNovoAtendimentoRecepcaoResponse,
  SalvarPacienteRecepcaoResponse
} from '../types'

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

export function listarProcedimentosRecepcao(q = '') {
  return $fetch<ListarProcedimentosRecepcaoResponse>(`/api/recepcao/procedimentos${queryParams({ q })}`)
}

export function listarConveniosRecepcao(q = '') {
  return $fetch<ListarConveniosRecepcaoResponse>(`/api/recepcao/convenios${queryParams({ q })}`)
}

export function listarMedicosRecepcao() {
  return $fetch<ListarMedicosRecepcaoResponse>('/api/recepcao/medicos')
}

export function buscarPacientesRecepcao(filtros: { q?: string, search?: string, cpf?: string, prontuario?: string, id?: string | number }) {
  return $fetch<BuscarPacientesRecepcaoResponse>(`/api/recepcao/pacientes/buscar${queryParams(filtros)}`)
}

export function salvarPacienteRecepcao(body: Record<string, unknown>) {
  return $fetch<SalvarPacienteRecepcaoResponse>('/api/recepcao/pacientes', {
    method: 'POST',
    body
  })
}

export function salvarAtendimentoRecepcao(body: Record<string, unknown>) {
  return $fetch('/api/recepcao/atendimentos', {
    method: 'POST',
    body
  })
}

export function salvarNovoAtendimentoRecepcao(body: Record<string, unknown>) {
  return $fetch<SalvarNovoAtendimentoRecepcaoResponse>('/api/recepcao/novo-atendimento', {
    method: 'POST',
    body
  })
}
