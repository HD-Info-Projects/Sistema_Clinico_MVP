import type {
  Agendamento,
  AgendamentoComPaciente,
  AgendamentoStatus,
  CheckInResponse,
  ExameConsultaPayload,
  MotivoNoShow,
  NoShowResponse,
  TipoProcedimentoTuss
} from '../types'

export type { CheckInResponse, MotivoNoShow, NoShowResponse, PacienteNoShow } from '../types'

export type AgendamentoComFiltro = {
  data?: string
  dataIni?: string
  dataFim?: string
  search?: string
  status?: AgendamentoStatus
  tipo?: TipoProcedimentoTuss
  clinicaId?: number
  medicoId?: number
}

export type ConsultaStatusPayload = {
  anamnese?: string
  diagnosticos?: { cid: string, descricao?: string, principal: boolean }[]
  medicamentos?: string
  exames?: ExameConsultaPayload[]
  duracao?: number
}

export type AtualizarStatusAgendamentoResponse = AgendamentoComPaciente | Agendamento

export function listarAgendamentos(filtros?: AgendamentoComFiltro) {
  const params = new URLSearchParams()
  if (filtros?.data) params.set('data', filtros.data)
  if (filtros?.dataIni) params.set('dataIni', filtros.dataIni)
  if (filtros?.dataFim) params.set('dataFim', filtros.dataFim)
  if (filtros?.search) params.set('search', filtros.search)
  if (filtros?.status) params.set('status', filtros.status)
  if (filtros?.tipo) params.set('tipo', filtros.tipo)
  if (filtros?.clinicaId) params.set('clinicaId', String(filtros.clinicaId))
  if (filtros?.medicoId) params.set('medicoId', String(filtros.medicoId))

  return $fetch<(Agendamento | AgendamentoComPaciente)[]>(`/api/agendamentos${params.toString() ? `?${params.toString()}` : ''}`)
}

export function atualizarStatusAgendamento(id: number, status: AgendamentoStatus, consulta?: ConsultaStatusPayload, clinicaId?: number) {
  const params = new URLSearchParams()
  if (clinicaId) params.set('clinicaId', String(clinicaId))
  const qs = params.toString()

  return $fetch<AgendamentoComPaciente>(`/api/agendamentos/${id}${qs ? `?${qs}` : ''}`, {
    method: 'PATCH',
    body: { status, consulta }
  })
}

export type MarcadorCalendarioResponse = {
  data?: string | null
  status?: Array<Exclude<AgendamentoStatus, 'cancelado'>> | Exclude<AgendamentoStatus, 'cancelado'> | null
  statuses?: Array<Exclude<AgendamentoStatus, 'cancelado'>> | null
}

export type BuscarMarcadoresParams = {
  data?: string
  dataIni?: string
  dataFim?: string
  sincronizar?: boolean | string
  clinicaId?: number
}

export function buscarMarcadores(filtros?: BuscarMarcadoresParams) {
  const params = new URLSearchParams()
  if (filtros?.data) params.set('data', filtros.data)
  if (filtros?.dataIni) params.set('dataIni', filtros.dataIni)
  if (filtros?.dataFim) params.set('dataFim', filtros.dataFim)
  if (filtros?.sincronizar !== undefined && filtros.sincronizar !== null && String(filtros.sincronizar) !== '' && String(filtros.sincronizar) !== 'false') {
    params.set('sincronizar', String(filtros.sincronizar))
  }
  if (filtros?.clinicaId) params.set('clinicaId', String(filtros.clinicaId))

  return $fetch<MarcadorCalendarioResponse[]>(`/api/agendamentos/marcadores${params.toString() ? `?${params.toString()}` : ''}`)
}

export function listarCheckIn(filtros?: Record<string, unknown>) {
  const params = new URLSearchParams()

  for (const key of ['page', 'pageSize', 'status', 'medico', 'q', 'data', 'unidadeId', 'tipo']) {
    const value = filtros?.[key]
    if (value !== undefined && value !== null && String(value).trim()) {
      params.set(key, String(value))
    }
  }

  return $fetch<CheckInResponse>(`/api/check-in${params.toString() ? `?${params.toString()}` : ''}`)
}

export function listarNoShow(filtros?: Record<string, unknown>) {
  const params = new URLSearchParams()

  for (const key of ['dataIni', 'dataFim', 'medico', 'especialidade', 'convenio', 'status', 'q', 'page', 'pageSize', 'unidadeId']) {
    const value = filtros?.[key]
    if (value !== undefined && value !== null && String(value).trim()) {
      params.set(key, String(value))
    }
  }

  return $fetch<NoShowResponse>(`/api/no-show${params.toString() ? `?${params.toString()}` : ''}`)
}

export function registrarMotivoNoShow(id: number, motivo: MotivoNoShow, unidadeId?: number) {
  const params = new URLSearchParams()
  if (unidadeId) params.set('unidadeId', String(unidadeId))
  const qs = params.toString()

  return $fetch<{ id: number, motivo: MotivoNoShow }>(`/api/no-show/${id}/motivo${qs ? `?${qs}` : ''}`, {
    method: 'PATCH',
    body: { motivo }
  })
}
