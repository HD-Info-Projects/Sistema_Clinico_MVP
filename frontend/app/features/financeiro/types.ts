export type PagamentoStatus = 'conciliado' | 'pendente' | 'divergente'

export type FormaPagamento = 'cartao-credito' | 'pix' | 'dinheiro' | 'cartao-debito'

export type PeriodoPagamento = 'hoje' | 'ontem' | 'ultimos-7-dias' | 'este-mes' | 'mes-anterior' | 'personalizado'

export interface PagamentosFiltrosForm {
  periodo: PeriodoPagamento
  paciente: string
  cpf: string
  status: PagamentoStatus | 'todos'
  dataIni: string
  dataFim: string
}

export interface Pagamento {
  id: string
  unidadeId: number
  data: string
  paciente: {
    id: number
    nome: string
    cpf: string
  }
  atendimento: {
    id: string
    descricao: string
  }
  formaPagamento: FormaPagamento
  valorBrutoCentavos: number
  status: PagamentoStatus
}

export interface PagamentosConsulta {
  unidadeId: number
  dataIni: string
  dataFim: string
  paciente?: string
  cpf?: string
  status?: PagamentoStatus
  page: number
  pageSize: number
}

export interface PagamentosResumo {
  conciliados: number
  pendentes: number
  divergentes: number
  totalBrutoCentavos: number
}

export interface PagamentosResponse {
  items: Pagamento[]
  total: number
  page: number
  pageSize: number
  resumo: PagamentosResumo
}
