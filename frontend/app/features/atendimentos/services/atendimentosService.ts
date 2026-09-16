export {
  atualizarStatusAgendamento as atualizarStatusAtendimento,
  listarAgendamentos as listarAtendimentosDashboard
} from '~/features/agenda/services/agendaService'

export type {
  AgendamentoComFiltro as AtendimentosDashboardFiltro,
  AtualizarStatusAgendamentoResponse,
  ConsultaStatusPayload
} from '~/features/agenda/services/agendaService'
