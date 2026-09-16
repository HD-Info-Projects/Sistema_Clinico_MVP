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

export function listarProcedimentosRecepcao(event: H3Event, query: Record<string, unknown>) {
  return flaskFetch(event, `/recepcao/procedimentos${queryParams(query, ['q'])}`)
}

export function listarConveniosRecepcao(event: H3Event, query: Record<string, unknown>) {
  return flaskFetch(event, `/recepcao/convenios${queryParams(query, ['q'])}`)
}

export function listarMedicosRecepcao(event: H3Event) {
  return flaskFetch(event, '/recepcao/medicos')
}

export function buscarPacientesRecepcao(event: H3Event, query: Record<string, unknown>) {
  return flaskFetch(event, `/recepcao/pacientes/buscar${queryParams(query, ['q', 'search', 'cpf', 'prontuario', 'id'])}`)
}

export function salvarPacienteRecepcao(event: H3Event, body: unknown) {
  return flaskFetch(event, '/recepcao/pacientes', {
    method: 'POST',
    body
  })
}

export function salvarAtendimentoRecepcao(event: H3Event, body: unknown) {
  return flaskFetch(event, '/recepcao/atendimentos', {
    method: 'POST',
    body,
    activeClinica: false
  })
}

export function salvarNovoAtendimentoRecepcao(event: H3Event, body: unknown) {
  return flaskFetch(event, '/recepcao/novo-atendimento', {
    method: 'POST',
    body,
    activeClinica: false
  })
}
