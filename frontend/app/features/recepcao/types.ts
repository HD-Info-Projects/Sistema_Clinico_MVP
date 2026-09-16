export type PacienteRecepcao = {
  idPacienteSpdata?: number
  nome: string
  nomeSocial?: string | null
  cpf?: string
  prontuario?: string
  dataNascimento?: string | null
  sexo?: string | null
  sexoBiologico?: string
  cidade?: string
  celular?: string
  celularWhatsapp?: string
  telefone?: string
  telefoneFixo?: string
  email?: string
  endereco?: string
  logradouro?: string
  numero?: string
  complemento?: string
  bairro?: string
  uf?: string
  estadoUf?: string
  cep?: string
  nomeMae?: string
  rg?: string
  orgaoEmissor?: string
  codigoIbge?: string
}

export type ProcedimentoRecepcao = {
  id: number
  spdataTpId?: number | null
  nome: string
  codigoProcedimento?: number | string | null
  codigoTuss?: number | string | null
}

export type ConvenioRecepcao = {
  idConvenioSpdata: number
  codigoSpdata?: number | null
  nome: string
  registroAns?: string | null
}

export type MedicoRecepcao = {
  id: number
  usuarioId?: number
  nome: string
  spdataId?: number | null
  crm?: string | null
  crmAtendimento?: string | null
  especialidade?: string | null
}

export type UnidadeRecepcao = {
  id: number
  nome: string
  codigoSpdataCentroCusto?: number | null
  codigo_spdata_centro_custo?: string | number | null
}

export type BuscarPacientesRecepcaoResponse = { pacientes: PacienteRecepcao[] }
export type ListarProcedimentosRecepcaoResponse = { procedimentos: ProcedimentoRecepcao[] }
export type ListarConveniosRecepcaoResponse = { convenios: ConvenioRecepcao[] }
export type ListarMedicosRecepcaoResponse = { medicos: MedicoRecepcao[] }
export type SalvarPacienteRecepcaoResponse = { paciente?: PacienteRecepcao, created?: boolean }
export type SalvarNovoAtendimentoRecepcaoResponse = { atendimentoCreated?: boolean }
