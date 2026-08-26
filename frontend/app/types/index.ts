export interface MedicamentoUso {
  nome: string
  dosagem: string
  frequencia: string
}

export interface HistoricoItem {
  data: string
  descricao: string
  diagnostico?: string
  medicamentos?: string
  exames?: string
}

export interface Paciente {
  id: number
  nome: string
  nomeSocial?: string | null
  encaixado: boolean
  sexo: 'masculino' | 'feminino'
  dataNascimento: string
  tipoSanguineo: string
  alergias: string[]
  medicamentosEmUso: MedicamentoUso[]
  convenio: string
  idConvenioSpdata?: number | null
  telefone: string
  email: string
  cpf: string
  endereco: string
  contatoEmergencia?: { nome: string, telefone: string, parentesco: string }
  responsavel?: { nome: string, telefone: string, parentesco: string }
  ultimaConsulta?: string
  historicoRecente: HistoricoItem[]
}

export interface Clinica {
  id: number
  nome: string
  slug?: string
  endereco: string
  telefone: string
  codigoSpdataCentroCusto?: number | null
  codigoSpdataAgenda?: string | null
}

export type AgendamentoStatus = 'agendado' | 'em-espera' | 'em-atendimento' | 'atendido' | 'faltou' | 'cancelado'

export type TipoProcedimentoTuss
  = 'consulta'
    | 'procedimento-ambulatorial'
    | 'cirurgia'
    | 'metodos-eletrofisiologicos'
    | 'endoscopia'
    | 'medicina-laboratorial'
    | 'medicina-transfusional'
    | 'genetica'
    | 'anatomia-patologica-citopatologia'
    | 'medicina-nuclear'
    | 'radiologia-rx'
    | 'ultrassonografia-us'
    | 'tomografia-computadorizada'
    | 'ressonancia-magnetica'
    | 'radioterapia'
    | 'exames-procedimentos-especificos'
    | 'testes-diagnostico'
    | 'outros-diagnosticos-terapeuticos'
    | 'outros'
    | 'nao-informado'

export interface Agendamento {
  id: number
  spdataAtendimentoId?: number | null
  spdataAgendaId?: number | null
  medsystemAtendimentoId?: number | null
  codAtendimento?: string | number | null
  pacienteId: number
  medicoId: number
  clinicaId: number
  data: string
  horario: string
  prioridade: 'normal' | 'preferencial'
  status: AgendamentoStatus
  descricao: string
  criadoEm: string
  duracao?: number
  codigoProcedimentoSpdata?: string | null
  procedimentoSpdata?: string | null
  tipoProcedimento?: TipoProcedimentoTuss
  tipoProcedimentoLabel?: string
}

export interface AgendamentoComPaciente extends Agendamento {
  paciente: Paciente
}

export type AgendaStatus = 'em-espera' | 'aguardando' | 'atendido' | 'falta' | 'presente'

export interface AgendaSlot {
  time: string
  type: 'appointment' | 'available' | 'lunch'
  patient?: {
    id: number
    name: string
    status: AgendaStatus
    description: string
    agendamentoId?: number
    statusOriginal?: string
  }
}

export interface AuthUser {
  id: number
  nome: string
  email: string
  role: 'medico' | 'recepcao' | 'admin' | 'dpo' | 'ti'
  especialidades?: string[]
  crm?: string
  clinicaIds: number[]
}

export interface ExameCatalogo {
  id: number
  nome: string
  codigo_alfanumerico: string | null
  codigo_amb: string | null
}

export interface ExameSelecionado {
  nome: string
  exameId: number | null
  codigo_amb?: string | null
  codigo_alfanumerico?: string | null
  orientacao?: string | null
}

export interface ProcedimentoCatalogo {
  id: number
  nome: string
  codigo_procedimento: number | null
  tipo_ato_codigo: number | null
  tipo_ato_nome: string | null
  apelido_procedimento?: string | null
  exige_autorizacao?: number | null
  qtde_max_guia?: number | null
}

export interface ProcedimentoSelecionado {
  procedimento_id: number | null
  nome: string
  codigo_procedimento?: number | null
  tipo_ato_codigo?: number | null
  tipo_ato_nome?: string | null
  exige_autorizacao?: number | null
  qtde_max_guia?: number | null
}

export interface ExameConsultaPayload {
  nome: string
  exame_id: number | null
  codigo_amb?: string | null
  codigo_alfanumerico?: string | null
  orientacao?: string | null
}

export interface HistoricoExame {
  nome: string
  exame_id: number | null
  descricao: string | null
  tipo_exame: string | null
  orientacao?: string | null
  codigo_alfanumerico: string | null
  codigo_amb: string | null
}

export interface ExameHistoricoItem {
  nome: string
  orientacao?: string | null
  temImagem: boolean
  temLaudo: boolean
  idTokenLancamentoExame?: number | null
}

export interface Chamado {
  id: number
  clinicaId: number
  pacienteId: number
  pacienteNome: string
  dataChamada: string
  status: 'chamando' | 'concluido' | 'cancelado'
  localAtendimento: string
  medicoResponsavel: string
}

export interface HistoricoRecord {
  ORIGEM?: 'BIODATA' | 'SPDATA' | null
  ANAMNESE?: string | null
  CID_PRINCIPAL: string | null
  CID_SECUNDARIO?: string | null
  CID_TERCIARIO?: string | null
  CID_QUATERNARIO?: string | null
  DATA_ANAMNESE?: string | null
  DATA_CONSULTA?: string | null
  DATA_ENCERRAMENTO?: string | null
  DIAGNOSTICO_PRINCIPAL: string | null
  DIAGNOSTICO_SECUNDARIO?: string | null
  ID_ANAMNESE?: string | null
  ID_ATENDIMENTO: string | null
  ID_EVOLUCAO: string | null
  ID_SOLICITACAO_EXAME: string | null
  ID_PACIENTE: number
  MEDICO: string | null
  MODELO_EVOLUCAO?: string | null
  OBS_ATENDIMENTO: string | null
  PACIENTE: string | null
  QUEIXA_PRINCIPAL?: string | null
}

export interface HistoricoResponse {
  items: HistoricoRecord[]
  limit: number
  offset: number
  has_more: boolean
}

export interface HistoricoLocalRecord {
  spdata_atendimento_id: number | null
  data_consulta: string | null
  medico_nome: string | null
  anamnese: string | null
  cid_principal: string | null
  cid_principal_descricao: string | null
  cids_secundarios: { codigo: string, descricao: string | null }[]
  medicamentos: string[]
  exames: (HistoricoExame | string)[]
}

export interface Atendimento {
  id: number
  pacienteId: number
  dataInicio: string
  dataFim?: string
  observacoes?: string
}

export type DocumentoMedicoTipo = 'ATESTADO' | 'ENCAMINHAMENTO' | 'SOLICITACAO_PROCEDIMENTO' | 'SOLICITACAO_OPME'

export interface DocumentoMedicoDadosBase {
  medico?: string | null
  crm?: string | null
  especialidade?: string | null
}

export interface AtestadoDocumentoDados extends DocumentoMedicoDadosBase {
  data_inicio: string
  dias_afastamento: number
}

export interface EncaminhamentoDocumentoDados extends DocumentoMedicoDadosBase {
  data: string
  encaminhar_para: string
  profissional_externo: string
}

export interface SolicitacaoProcedimentoDocumentoDados extends DocumentoMedicoDadosBase {
  data: string
  descricao: string
  procedimentos?: ProcedimentoSelecionado[]
  caraterInternacao?: boolean
  tipoInternacao?: string
  regimeInternacao?: string
  quantidadeDiarias?: number
  indicacaoClinica?: string
  atendimentoRN?: boolean
  cids?: { cid: string, nome: string }[]
}

export interface SolicitacaoOpmeDocumentoDados extends DocumentoMedicoDadosBase {
  data: string
  opmeSolicitados?: string
  opmeItens?: { codigo?: string, nome: string, quantidade?: number }[]
  indicacaoClinica?: string
}

export type DocumentoMedicoDados = AtestadoDocumentoDados | EncaminhamentoDocumentoDados | SolicitacaoProcedimentoDocumentoDados | SolicitacaoOpmeDocumentoDados

export interface DocumentoMedico {
  id: number
  atendimentoId: number
  medSpdataAtendimentoId: number
  tipoDocumento: DocumentoMedicoTipo
  dados: DocumentoMedicoDados
  createdAt: string | null
  updatedAt: string | null
  podeEditar: boolean
}

export interface ItemMedicamento {
  nome: string
  dosagem: string
  detalhes: string
}

export interface PadraoReceita {
  id: string
  medicoId: number
  nome: string
  tipo: 'receita'
  medicamentos: ItemMedicamento[]
  createdAt: string
  updatedAt: string
}

export interface PadraoExame {
  id: string
  medicoId: number
  nome: string
  tipo: 'exame'
  exames: ExameSelecionado[]
  createdAt: string
  updatedAt: string
}

export interface PadraoAnamnese {
  id: string
  medicoId: number
  nome: string
  conteudo: string
  createdAt: string
  updatedAt: string
}

export interface PadraoOrientacaoExame {
  id: string
  medicoId: number
  nome: string
  conteudo: string
  createdAt: string
  updatedAt: string
}

export type Padrao = PadraoReceita | PadraoExame

export interface Usuario {
  id: number
  nome_completo: string
  cnpj_cpf: string
  email: string
  role: 'medico' | 'recepcao' | 'admin'
  ativo?: boolean
  created_at: string
  updated_at: string
  medico?: Medico
  unidades?: Clinica[]
  unidade_ids?: number[]
}

export interface Medico {
  id: number
  usuario_id: number
  spdata_id?: number | null
  crm?: string | null
  crm_atendimento_spdata?: string | null
  crm_uf?: string | null
  rqe?: string | null
  especialidade?: string | null
  ativo: boolean
}

export interface UsuarioForm {
  nome_completo: string
  cnpj_cpf: string
  email: string
  senha?: string
  role: 'medico' | 'recepcao' | 'admin'
  ativo?: boolean
  unidade_ids?: number[]
  medico?: {
    spdata_id?: number | null
    crm?: string
    crm_uf?: string
    crm_atendimento_spdata?: string
    rqe?: string
    especialidade?: string
    ativo?: boolean
  }
}

export type RoleUsuario = 'medico' | 'recepcao' | 'admin'

export interface MedicoSpdata {
  spdata_id: number
  nome: string
  documento: string
  email?: string | null
  crm?: string | null
  crm_uf?: string | null
  crm_atendimento_spdata?: string | null
  especialidade?: string | null
}

export interface Unidade {
  id: number
  nome: string
  slug: string
  codigo_spdata_centro_custo: string
  codigo_spdata_agenda: string
  endereco: string
  telefone: string
  ativa: boolean
  created_at: string
  updated_at: string
}

export interface UnidadeForm {
  nome: string
  codigo_spdata_centro_custo: string
  codigo_spdata_agenda: string
  endereco: string
  telefone: string
  ativa: boolean
}
