import type {
  ExamePacs,
  ExamesPacsResponse,
  HistoricoExame,
  HistoricoItem,
  HistoricoLocalRecord,
  HistoricoRecord,
  HistoricoResponse,
  MedicamentoUso,
  Paciente
} from '~/types'

export type {
  ExamePacs,
  ExamesPacsResponse,
  HistoricoExame,
  HistoricoItem,
  HistoricoLocalRecord,
  HistoricoRecord,
  HistoricoResponse,
  MedicamentoUso,
  Paciente
}

export interface PacienteFila {
  id: number
  pacienteId: number
  medicoId: number
  clinicaId: number
  data: string
  horario: string
  prioridade: 'normal'
  status: 'em-espera'
  descricao: string
  criadoEm: string
  paciente: Paciente
}

export type CidResultado = { cid: string, nome: string }

export type FiltrosHistoricoLocal = {
  cpf?: string
  nome?: string
  spdataAtendimentoId?: number | string
  data?: string
}

export type FiltrosHistoricoExterno = {
  cpf?: string
  nome?: string
  spdataAtendimentoId?: number | string
  limit?: number
  offset?: number
}

export type FiltrosPacientes = {
  search?: string
  data?: string
}

export type FiltrosCid = {
  q?: string
  limit?: number
  offset?: number
}
