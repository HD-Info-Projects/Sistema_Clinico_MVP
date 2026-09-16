import type { H3Event } from 'h3'
import { flaskFetch } from '../../utils/flask'

export function listarAgenda(event: H3Event, query: Record<string, unknown>) {
  const params = new URLSearchParams()

  for (const key of ['data', 'dataIni', 'dataFim', 'search', 'status', 'tipo']) {
    const value = query[key]
    if (value !== undefined && value !== null && String(value).trim()) {
      params.set(key, String(value))
    }
  }

  return flaskFetch(event, `/agenda-medica/${params.toString() ? `?${params.toString()}` : ''}`)
}

export function listarMarcadoresAgenda(event: H3Event, query: Record<string, unknown>) {
  const params = new URLSearchParams()

  for (const key of ['data', 'dataIni', 'dataFim', 'sincronizar']) {
    const value = query[key]
    if (value !== undefined && value !== null && String(value).trim()) {
      params.set(key, String(value))
    }
  }

  return flaskFetch(event, `/agenda-medica/marcadores${params.toString() ? `?${params.toString()}` : ''}`)
}

export type AtualizarStatusResultado = {
  id?: number
  status?: string
  pacienteId?: number
}

export function atualizarStatusAgenda(event: H3Event, id: number, body: unknown) {
  return flaskFetch<AtualizarStatusResultado>(event, `/agenda-medica/${id}/status`, {
    method: 'PATCH',
    body
  })
}

export function listarCheckIn(event: H3Event, query: Record<string, unknown>) {
  const params = new URLSearchParams()

  for (const key of ['page', 'pageSize', 'status', 'medico', 'q', 'data', 'unidadeId', 'tipo']) {
    const value = query[key]
    if (value !== undefined && value !== null && String(value).trim()) {
      params.set(key, String(value))
    }
  }

  const qs = params.toString()
  return flaskFetch(event, `/check_in/${qs ? `?${qs}` : ''}`)
}

export function listarNoShow(event: H3Event, query: Record<string, unknown>) {
  const params = new URLSearchParams()

  for (const key of ['dataIni', 'dataFim', 'medico', 'especialidade', 'convenio', 'status', 'q', 'page', 'pageSize', 'unidadeId']) {
    const value = query[key]
    if (value !== undefined && value !== null && String(value).trim()) {
      params.set(key, String(value))
    }
  }

  const qs = params.toString()
  return flaskFetch(event, `/no_show/${qs ? `?${qs}` : ''}`)
}

export function registrarMotivoNoShow(event: H3Event, id: number, body: { motivo: string }) {
  return flaskFetch(event, `/no_show/${id}/motivo`, {
    method: 'PATCH',
    body
  })
}
