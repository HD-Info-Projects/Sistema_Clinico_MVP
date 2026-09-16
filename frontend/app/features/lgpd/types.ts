export type AuditoriaUsuario = {
  id: number
  nome_completo: string
  email: string
  role: string
}

export type AuditoriaEvento = {
  id: number
  usuario_id: number | null
  medico_id: number | null
  acao: string
  entidade: string | null
  entidade_id: number | null
  descricao: string | null
  ip: string | null
  user_agent: string | null
  created_at: string | null
  usuario: AuditoriaUsuario | null
}

export type AuditoriaResponse = {
  items: AuditoriaEvento[]
  limit: number
  offset: number
  has_more: boolean
}

export type AuditoriaFiltros = {
  dataIni?: string
  dataFim?: string
  acao?: string
  entidade?: string
  usuarioId?: number | string
  limit?: number
  offset?: number
}

export type ExameRetencao = {
  id: number
  spdataExameId?: number
  spdataContaId?: number
  spdataAtendimentoId?: number | null
  paciente: string
  cpf: string
  prontuario: string
  convenio: string
  medico: string
  crm: string
  especialidade: string
  exame: string
  codigoTuss: string
  dataSolicitacao: string
  diasEmAberto: number
  status: 'pendente' | 'realizado' | 'nao-convertido'
  valorEstimado: number
  valorRealizado: number | null
  ultimoContato: string | null
  responsavel: string | null
  telefone: string
  guia?: string
  senha?: string
  dataColeta?: string
  dataLiberacao?: string
  pendencia?: string
  statusSpdata?: string
}

export type RetencaoExamesResponse = {
  items: ExameRetencao[]
  dataIni: string
  dataFim: string
}

export type RetencaoExamesFiltros = {
  dataIni: string
  dataFim: string
  unidadeId?: number | string
}

export type ContatoRetencao = {
  data: string
  canal: string
  usuario: string
  resultado: string
  observacao: string
}
