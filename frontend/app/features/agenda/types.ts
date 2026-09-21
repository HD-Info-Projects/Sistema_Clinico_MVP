import type { Agendamento, AgendamentoComPaciente, AgendamentoStatus, ExameConsultaPayload, Paciente, TipoProcedimentoTuss } from '~/types'

export type { Agendamento, AgendamentoComPaciente, AgendamentoStatus, ExameConsultaPayload, Paciente, TipoProcedimentoTuss }

export type MarcadorAgenda = Exclude<AgendamentoStatus, 'cancelado'>

export type AtendimentoStatusRecepcao = 'agendado' | 'em-espera' | 'em-atendimento' | 'atendido' | 'faltou' | 'desconhecido'

export interface AtendimentoRecepcao {
  id: number | string
  registro: string
  horario: string
  paciente: string
  cpf: string
  prontuario: string
  convenio: string
  telefone: string
  celular: string
  email: string
  medico: string
  especialidade: string
  codigoProcedimentoSpdata: string | null
  tipoProcedimento: TipoProcedimentoTuss
  tipoProcedimentoLabel: string
  dataNascimento: string | null
  idade: number | null
  status: AtendimentoStatusRecepcao
}

export interface MedicoDia {
  id: string
  nome: string
  especialidade: string
  pacientesCount: number
}

export interface ResumoRecepcao {
  agendados: number
  emEspera: number
  emAtendimento: number
  atendidos: number
  faltas: number
  desconhecidos: number
}

export interface CheckInResponse {
  items: AtendimentoRecepcao[]
  page: number
  pageSize: number
  total: number
  medicos: MedicoDia[]
  resumo: ResumoRecepcao
  data: string
}

export type MotivoNoShow = 'esquecimento' | 'transporte' | 'outros'

export interface PacienteNoShow {
  id: number
  spdataAgendaId: number
  medsystemAtendimentoId: number | null
  nome: string
  telefone: string
  convenio: string
  medico: string
  especialidade: string
  dataFalta: string
  horario: string
  status: 'nao-confirmado' | 'faltou'
  situacao: string
  motivo: MotivoNoShow | null
  recuperado: boolean
  cpf: string
  prontuario: string
}

export interface NoShowResponse {
  items: PacienteNoShow[]
  total: number
  page: number
  pageSize: number
  resumo: {
    totalResgate: number
    faltou: number
    naoConfirmado: number
    recuperados: number
    semContato: number
  }
  filtros: {
    medicos: string[]
    especialidades: string[]
    convenios: string[]
    anos: string[]
  }
  graficos: {
    porMes: Array<{ label: string, total: number }>
    porEspecialidade: Array<{ label: string, total: number }>
    porDiaSemana: Array<{ label: string, total: number }>
  }
}
