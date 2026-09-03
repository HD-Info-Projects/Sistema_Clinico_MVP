<script setup lang="ts">
import { CalendarDate, type Time } from '@internationalized/date'
import { formatarCpf, formatarCpfCnpj, formatarTelefone } from '~/utils/masks'

type PacienteRecepcao = {
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

type EnderecoViaCep = { erro?: boolean, logradouro?: string, complemento?: string, bairro?: string, localidade?: string, uf?: string, ibge?: string }

type ProcedimentoRecepcao = {
  id: number
  spdataTpId?: number | null
  nome: string
  codigoProcedimento?: number | string | null
  codigoTuss?: number | string | null
}

type ConvenioRecepcao = {
  idConvenioSpdata: number
  codigoSpdata?: number | null
  nome: string
  registroAns?: string | null
}

type MedicoRecepcao = {
  id: number
  usuarioId?: number
  nome: string
  spdataId?: number | null
  crm?: string | null
  crmAtendimento?: string | null
  especialidade?: string | null
}

type UnidadeRecepcao = {
  id: number
  nome: string
  codigoSpdataCentroCusto?: number | null
  codigo_spdata_centro_custo?: string | number | null
}

const auth = useAuthStore()
const toast = useToast()
const userName = computed(() => auth.user?.nome || 'Usuário')
const tabAtiva = ref('paciente')
const pacienteConcluido = ref(false)
const atendimentoConcluido = ref(false)
const pacienteSelecionado = ref<PacienteRecepcao | null>(null)
const fotoPaciente = ref<File | null>(null)
const fotoPacienteUrl = ref<string | null>(null)
const dataNascimento = shallowRef<CalendarDate | null>(null)
const dataEntrada = shallowRef<CalendarDate | null>(null)
const horaEntrada = shallowRef<Time | null>(null)
const dataNascimentoResponsavel = shallowRef<CalendarDate | null>(null)
const cepBuscando = ref(false)
const cepErro = ref('')
const cameraAberta = ref(false)
const cameraCarregando = ref(false)
const cameraErro = ref('')
const videoCamera = ref<HTMLVideoElement | null>(null)
let streamCamera: MediaStream | null = null
let consultaCepTimer: ReturnType<typeof setTimeout> | null = null
let buscaPacienteTimer: ReturnType<typeof setTimeout> | null = null
let buscaProcedimentoTimer: ReturnType<typeof setTimeout> | null = null
let buscaConvenioTimer: ReturnType<typeof setTimeout> | null = null
let consultaCepAtual = 0
const prontuarioNovo = ref('')
const pacientesEncontrados = ref<PacienteRecepcao[]>([])
const pacienteSpdataId = ref<number | null>(null)
const procedimentos = ref<ProcedimentoRecepcao[]>([])
const convenios = ref<ConvenioRecepcao[]>([])
const medicos = ref<MedicoRecepcao[]>([])
const buscaTermoProcedimento = ref('')
const buscaTermoConvenio = ref('')
const carregandoProcedimentos = ref(false)
const carregandoConvenios = ref(false)
const carregandoMedicos = ref(false)

const paciente = reactive({
  nomeCompleto: '', nomeSocial: '', cpf: '', nomeMae: '', rg: '', orgaoEmissor: '', sexoBiologico: '', identidadeGenero: '', estadoCivil: '', nacionalidade: '', naturalidade: '', celularWhatsapp: '', telefoneFixo: '', email: '', cep: '', logradouro: '', numero: '', complemento: '', bairro: '', cidade: '', estadoUf: '', codigoIbge: ''
})
const atendimento = reactive({
  registro: '', caraterSolicitacao: '', codigoProcedimento: '', nomeProcedimento: '', tipoProcedimento: '', modalidade: '', ehRetorno: false, recemNascido: false, atualizaFaturamento: false, numeroConvenio: '', descricaoConvenio: '', matricula: '', validade: '', guiaAutorizacao: '', crm: '', nomeMedico: '', especialidade: '', centroCustoNumero: '', centroCustoNome: '', unidade: '', procedimentoId: null as number | null, procedimentoIdSpdata: null as number | null, idConvenioSpdata: null as number | null, medicoId: null as number | null, medicoSpdataId: null as number | null, unidadeId: null as number | null
})
const responsavel = reactive({
  nome: '', identidade: '', cpf: '', cnpj: '', parentesco: '', cep: '', logradouro: '', numero: '', complemento: '', bairro: '', cidade: '', uf: '', telefone: '', profissao: ''
})

const opcoesSexo = [{ label: 'Masculino', value: 'masculino' }, { label: 'Feminino', value: 'feminino' }, { label: 'Intersexo', value: 'intersexo' }, { label: 'Prefiro não informar', value: 'nao_informar' }]
const opcoesGenero = [{ label: 'Mulher cisgênero', value: 'mulher_cisgenero' }, { label: 'Homem cisgênero', value: 'homem_cisgenero' }, { label: 'Mulher transgênero', value: 'mulher_transgenero' }, { label: 'Homem transgênero', value: 'homem_transgenero' }, { label: 'Não binário', value: 'nao_binario' }, { label: 'Outra', value: 'outra' }, { label: 'Prefiro não informar', value: 'nao_informar' }]
const opcoesEstadoCivil = ['Solteiro(a)', 'Casado(a)', 'União estável', 'Divorciado(a)', 'Viúvo(a)', 'Prefiro não informar']
const estadosBr = ['AC', 'AL', 'AP', 'AM', 'BA', 'CE', 'DF', 'ES', 'GO', 'MA', 'MT', 'MS', 'MG', 'PA', 'PB', 'PR', 'PE', 'PI', 'RJ', 'RN', 'RS', 'RO', 'RR', 'SC', 'SP', 'SE', 'TO']
const opcoesCarater = ['Eletiva', 'Urgência', 'Emergência']
const opcoesTipo = ['Consulta', 'Exame', 'Procedimento', 'Terapia']
const opcoesModalidade = ['Ambulatorial', 'Hospitalar', 'Domiciliar', 'Teleatendimento']

const tabItems = computed(() => [
  { label: 'Paciente', value: 'paciente', icon: 'i-lucide-user-round', slot: 'paciente' },
  { label: 'Atendimento', value: 'atendimento', icon: 'i-lucide-stethoscope', slot: 'atendimento', disabled: !pacienteConcluido.value },
  { label: 'Responsável', value: 'responsavel', icon: 'i-lucide-users', slot: 'responsavel', disabled: !atendimentoConcluido.value }
])
const sugestoesPacientes = computed(() => pacientesEncontrados.value.map(p => ({ label: p.nome, cpf: p.cpf, prontuario: p.prontuario, onSelect: () => selecionarPaciente(p) })))
const unidadesAtendimento = computed(() => auth.clinicas as UnidadeRecepcao[])
const sugestoesProcedimentos = computed(() => procedimentos.value.map(procedimento => ({
  label: procedimentoLabel(procedimento),
  codigo: String(procedimento.codigoProcedimento ?? procedimento.codigoTuss ?? procedimento.spdataTpId ?? ''),
  codigoTuss: String(procedimento.codigoTuss ?? ''),
  nome: procedimento.nome,
  onSelect: () => selecionarProcedimento(procedimento)
})))
const sugestoesConvenios = computed(() => convenios.value.map(convenio => ({
  label: convenio.nome,
  codigo: String(convenio.idConvenioSpdata ?? convenio.codigoSpdata ?? ''),
  registroAns: convenio.registroAns ?? '',
  onSelect: () => selecionarConvenio(convenio)
})))
const sugestoesMedicos = computed(() => medicos.value.map(medico => ({
  label: medico.nome,
  crm: String(medico.crmAtendimento || medico.crm || ''),
  especialidade: medico.especialidade || '',
  onSelect: () => selecionarMedico(medico)
})))
const sugestoesUnidades = computed(() => unidadesAtendimento.value.map(unidade => ({
  label: unidade.nome,
  codigo: String(codigoCentroCustoUnidade(unidade) ?? ''),
  onSelect: () => selecionarUnidade(unidade)
})))
const prontuarioAtual = computed(() => pacienteSelecionado.value?.prontuario || prontuarioNovo.value || 'Será gerado ao avançar')
const idadePaciente = computed(() => {
  const data = dataNascimento.value
  const dataSelecionada = pacienteSelecionado.value?.dataNascimento
  const nasc = dataSelecionada
    ? new Date(`${dataSelecionada}T12:00:00`)
    : data ? new Date(`${data.year}-${String(data.month).padStart(2, '0')}-${String(data.day).padStart(2, '0')}T12:00:00`) : null
  if (!nasc || Number.isNaN(nasc.getTime())) return ''
  const hoje = new Date()
  let idade = hoje.getFullYear() - nasc.getFullYear()
  if (hoje.getMonth() < nasc.getMonth() || (hoje.getMonth() === nasc.getMonth() && hoje.getDate() < nasc.getDate())) idade--
  return `${idade} anos`
})

function limparEtapasSeguintes() {
  Object.assign(atendimento, { registro: '', caraterSolicitacao: '', codigoProcedimento: '', nomeProcedimento: '', tipoProcedimento: '', modalidade: '', ehRetorno: false, recemNascido: false, atualizaFaturamento: false, numeroConvenio: '', descricaoConvenio: '', matricula: '', validade: '', guiaAutorizacao: '', crm: '', nomeMedico: '', especialidade: '', centroCustoNumero: '', centroCustoNome: '', unidade: '', procedimentoId: null, procedimentoIdSpdata: null, idConvenioSpdata: null, medicoId: null, medicoSpdataId: null, unidadeId: null })
  aplicarUnidadeAtiva()
  Object.assign(responsavel, { nome: '', identidade: '', cpf: '', cnpj: '', parentesco: '', cep: '', logradouro: '', numero: '', complemento: '', bairro: '', cidade: '', uf: '', telefone: '', profissao: '' })
  dataEntrada.value = null
  horaEntrada.value = null
  dataNascimentoResponsavel.value = null
  atendimentoConcluido.value = false
}

function mensagemErro(error: unknown, fallback: string) {
  const err = error as { data?: { error?: string, message?: string }, message?: string }
  return err.data?.error || err.data?.message || err.message || fallback
}

function dataCalendarIso(data: CalendarDate | null) {
  if (!data) return null
  return `${data.year}-${String(data.month).padStart(2, '0')}-${String(data.day).padStart(2, '0')}`
}

function horaIso(hora: Time | null) {
  if (!hora) return ''
  return `${String(hora.hour).padStart(2, '0')}:${String(hora.minute).padStart(2, '0')}`
}

function payloadPaciente() {
  return {
    ...paciente,
    idPacienteSpdata: pacienteSpdataId.value ?? pacienteSelecionado.value?.idPacienteSpdata,
    dataNascimento: dataCalendarIso(dataNascimento.value)
  }
}

function payloadAtendimento() {
  return {
    ...atendimento,
    unidadeId: atendimento.unidadeId ?? auth.activeClinicaId,
    idPacienteSpdata: pacienteSpdataId.value ?? pacienteSelecionado.value?.idPacienteSpdata,
    dataEntrada: dataCalendarIso(dataEntrada.value),
    horaEntrada: horaIso(horaEntrada.value)
  }
}

function procedimentoLabel(procedimento: ProcedimentoRecepcao) {
  const codigo = procedimento.codigoTuss || procedimento.codigoProcedimento
  return codigo ? `${procedimento.nome} - ${codigo}` : procedimento.nome
}

function codigoCentroCustoUnidade(unidade: UnidadeRecepcao) {
  return unidade.codigoSpdataCentroCusto ?? unidade.codigo_spdata_centro_custo ?? null
}

function selecionarProcedimento(procedimento: ProcedimentoRecepcao) {
  atendimento.procedimentoId = procedimento.id
  atendimento.procedimentoIdSpdata = procedimento.spdataTpId ?? null
  atendimento.codigoProcedimento = String(procedimento.codigoProcedimento ?? procedimento.codigoTuss ?? '')
  atendimento.nomeProcedimento = procedimento.nome
}

function selecionarConvenio(convenio: ConvenioRecepcao) {
  atendimento.idConvenioSpdata = convenio.idConvenioSpdata
  atendimento.numeroConvenio = String(convenio.idConvenioSpdata ?? convenio.codigoSpdata ?? '')
  atendimento.descricaoConvenio = convenio.nome
}

function selecionarMedico(medico: MedicoRecepcao) {
  atendimento.medicoId = medico.id
  atendimento.medicoSpdataId = medico.spdataId ?? null
  atendimento.crm = medico.crmAtendimento || medico.crm || ''
  atendimento.nomeMedico = medico.nome
  atendimento.especialidade = medico.especialidade || ''
}

function selecionarUnidade(unidade: UnidadeRecepcao) {
  atendimento.unidadeId = unidade.id
  atendimento.centroCustoNumero = String(codigoCentroCustoUnidade(unidade) ?? '')
  atendimento.centroCustoNome = unidade.nome
  atendimento.unidade = unidade.nome
  if (auth.activeClinicaId !== unidade.id) void auth.setActiveClinica(unidade.id)
}

function aplicarUnidadeAtiva() {
  const unidade = unidadesAtendimento.value.find(item => item.id === auth.activeClinicaId)
  if (unidade) selecionarUnidade(unidade)
}

async function carregarProcedimentos(q = '') {
  carregandoProcedimentos.value = true
  try {
    const params = q.trim() ? `?q=${encodeURIComponent(q.trim())}` : ''
    const response = await $fetch<{ procedimentos: ProcedimentoRecepcao[] }>(`/api/recepcao/procedimentos${params}`)
    procedimentos.value = response.procedimentos ?? []
  } catch (error) {
    toast.add({ title: mensagemErro(error, 'Não foi possível carregar procedimentos.'), color: 'error' })
  } finally {
    carregandoProcedimentos.value = false
  }
}

async function carregarConvenios(q = '') {
  carregandoConvenios.value = true
  try {
    const params = q.trim() ? `?q=${encodeURIComponent(q.trim())}` : ''
    const response = await $fetch<{ convenios: ConvenioRecepcao[] }>(`/api/recepcao/convenios${params}`)
    convenios.value = response.convenios ?? []
  } catch (error) {
    toast.add({ title: mensagemErro(error, 'Não foi possível carregar convênios.'), color: 'error' })
  } finally {
    carregandoConvenios.value = false
  }
}

async function carregarMedicos() {
  carregandoMedicos.value = true
  try {
    const response = await $fetch<{ medicos: MedicoRecepcao[] }>('/api/recepcao/medicos')
    medicos.value = response.medicos ?? []
  } catch (error) {
    toast.add({ title: mensagemErro(error, 'Não foi possível carregar médicos.'), color: 'error' })
  } finally {
    carregandoMedicos.value = false
  }
}

async function carregarOpcoesAtendimento() {
  aplicarUnidadeAtiva()
  await Promise.all([
    carregarProcedimentos(),
    carregarConvenios(),
    carregarMedicos()
  ])
}

function payloadResponsavel() {
  return {
    ...responsavel,
    dataNascimento: dataCalendarIso(dataNascimentoResponsavel.value)
  }
}

async function buscarPacientesSpdata(termo: string) {
  const q = termo.trim()
  if (q.length < 3) {
    pacientesEncontrados.value = []
    return
  }

  try {
    const response = await $fetch<{ pacientes: PacienteRecepcao[] }>(`/api/recepcao/pacientes/buscar?q=${encodeURIComponent(q)}`)
    pacientesEncontrados.value = response.pacientes ?? []
  } catch {
    pacientesEncontrados.value = []
  }
}

async function salvarPacienteSpdata() {
  const response = await $fetch<{ paciente?: PacienteRecepcao, created?: boolean }>('/api/recepcao/pacientes', {
    method: 'POST',
    body: payloadPaciente()
  })
  const salvo = response.paciente
  if (!salvo?.idPacienteSpdata) throw new Error('SPDATA não retornou o paciente salvo')

  pacienteSpdataId.value = salvo.idPacienteSpdata
  pacienteSelecionado.value = salvo
  prontuarioNovo.value = salvo.prontuario || prontuarioNovo.value
  return response
}

function aplicarPacienteSelecionado(item: PacienteRecepcao) {
  pacienteSpdataId.value = item.idPacienteSpdata ?? null
  Object.assign(paciente, {
    nomeCompleto: item.nome || '',
    nomeSocial: item.nomeSocial || '',
    cpf: item.cpf ? formatarCpf(item.cpf) : '',
    sexoBiologico: item.sexoBiologico || item.sexo || '',
    cidade: item.cidade || '',
    celularWhatsapp: item.celularWhatsapp || item.celular || '',
    telefoneFixo: item.telefoneFixo || item.telefone || '',
    email: item.email || '',
    logradouro: item.logradouro || item.endereco || '',
    numero: item.numero || '',
    complemento: item.complemento || '',
    bairro: item.bairro || '',
    estadoUf: item.estadoUf || item.uf || '',
    cep: item.cep ? formatarCep(item.cep) : '',
    nomeMae: item.nomeMae || '',
    rg: item.rg || '',
    orgaoEmissor: item.orgaoEmissor || '',
    codigoIbge: item.codigoIbge || ''
  })
}

function selecionarPaciente(item: PacienteRecepcao) {
  pacienteSelecionado.value = item
  if (item.dataNascimento) {
    const [ano, mes, dia] = item.dataNascimento.split('-').map(Number)
    dataNascimento.value = new CalendarDate(ano!, mes!, dia!)
  }
  prontuarioNovo.value = ''
  aplicarPacienteSelecionado(item)
  limparEtapasSeguintes()
}

function iniciarPacienteNovo() {
  if (!pacienteSelecionado.value) return
  pacienteSelecionado.value = null
  pacienteSpdataId.value = null
  prontuarioNovo.value = ''
  limparEtapasSeguintes()
}

async function proximoPaciente() {
  if (!paciente.nomeCompleto.trim()) {
    toast.add({ title: 'Informe o nome completo do paciente.', color: 'error' })
    return
  }
  if (!auth.activeClinicaId) {
    toast.add({ title: 'Selecione uma unidade antes de continuar.', color: 'error' })
    return
  }

  try {
    const response = await salvarPacienteSpdata()
    const salvo = response.paciente
    if (salvo?.prontuario) prontuarioNovo.value = salvo.prontuario
    pacienteConcluido.value = true
    tabAtiva.value = 'atendimento'
    void carregarOpcoesAtendimento()
    toast.add({
      title: response.created ? 'Paciente cadastrado no SPDATA.' : 'Paciente atualizado no SPDATA.',
      description: salvo?.prontuario ? `Prontuário ${salvo.prontuario}` : undefined,
      color: 'success'
    })
  } catch (error) {
    toast.add({ title: mensagemErro(error, 'Não foi possível salvar o paciente no SPDATA.'), color: 'error' })
  }
}

function validarAtendimento() {
  if (!auth.activeClinicaId) return 'Selecione uma unidade antes de criar o atendimento.'
  if (!pacienteSpdataId.value && !pacienteSelecionado.value?.idPacienteSpdata) return 'Salve o paciente antes de criar o atendimento.'
  if (!dataEntrada.value) return 'Informe a data de entrada.'
  if (!horaEntrada.value) return 'Informe a hora de entrada.'
  if (!atendimento.crm.trim() && !atendimento.nomeMedico.trim()) return 'Informe o CRM ou o nome do médico.'
  return null
}

function proximoAtendimento() {
  const erro = validarAtendimento()
  if (erro) {
    toast.add({ title: erro, color: 'error' })
    return
  }

  atendimentoConcluido.value = true
  tabAtiva.value = 'responsavel'
}

async function finalizarCadastro() {
  const erro = validarAtendimento()
  if (erro) {
    toast.add({ title: erro, color: 'error' })
    tabAtiva.value = 'atendimento'
    return
  }

  try {
    const response = await $fetch<{ atendimentoCreated?: boolean }>('/api/recepcao/novo-atendimento', {
      method: 'POST',
      body: {
        unidadeId: atendimento.unidadeId ?? auth.activeClinicaId,
        paciente: payloadPaciente(),
        atendimento: payloadAtendimento(),
        responsavel: payloadResponsavel()
      }
    })

    toast.add({
      title: response.atendimentoCreated ? 'Atendimento criado no SPDATA.' : 'Atendimento já existia no SPDATA.',
      description: 'Ele aparecerá como em espera para recepção e médico.',
      color: 'success'
    })
    await navigateTo('/recepcao')
  } catch (error) {
    toast.add({ title: mensagemErro(error, 'Não foi possível finalizar o cadastro no SPDATA.'), color: 'error' })
  }
}

function formatarCep(valor: string) {
  const digitos = valor.replace(/\D/g, '').slice(0, 8)
  return digitos.length > 5 ? `${digitos.slice(0, 5)}-${digitos.slice(5)}` : digitos
}

async function buscarEnderecoPorCep(cep: string, consulta: number) {
  cepBuscando.value = true
  cepErro.value = ''
  try {
    const endereco = await $fetch<EnderecoViaCep>(`https://viacep.com.br/ws/${cep}/json/`)
    if (consulta !== consultaCepAtual) return
    if (endereco.erro) {
      cepErro.value = 'CEP não encontrado.'
      return
    }
    paciente.logradouro = endereco.logradouro ?? ''
    paciente.complemento = endereco.complemento ?? ''
    paciente.bairro = endereco.bairro ?? ''
    paciente.cidade = endereco.localidade ?? ''
    paciente.estadoUf = endereco.uf ?? ''
    paciente.codigoIbge = endereco.ibge ?? ''
  } catch {
    if (consulta === consultaCepAtual) cepErro.value = 'Não foi possível consultar o CEP. Tente novamente.'
  } finally {
    if (consulta === consultaCepAtual) cepBuscando.value = false
  }
}

function encerrarCamera() {
  streamCamera?.getTracks().forEach(track => track.stop())
  streamCamera = null
  if (videoCamera.value) videoCamera.value.srcObject = null
}

async function abrirCamera() {
  cameraErro.value = ''
  cameraAberta.value = true
  if (!navigator.mediaDevices?.getUserMedia) {
    cameraErro.value = 'A câmera não está disponível neste navegador.'
    return
  }
  cameraCarregando.value = true
  try {
    streamCamera = await navigator.mediaDevices.getUserMedia({ video: { facingMode: 'user' }, audio: false })
    await nextTick()
    if (videoCamera.value) {
      videoCamera.value.srcObject = streamCamera
      await videoCamera.value.play()
    }
  } catch {
    cameraErro.value = 'Não foi possível acessar a câmera. Verifique a permissão do navegador.'
    encerrarCamera()
  } finally {
    cameraCarregando.value = false
  }
}

function fecharCamera() {
  cameraAberta.value = false
  encerrarCamera()
}

function capturarFoto() {
  const video = videoCamera.value
  if (!video?.videoWidth || !video.videoHeight) return
  const tamanho = Math.min(video.videoWidth, video.videoHeight)
  const canvas = document.createElement('canvas')
  canvas.width = tamanho
  canvas.height = tamanho
  canvas.getContext('2d')?.drawImage(video, (video.videoWidth - tamanho) / 2, (video.videoHeight - tamanho) / 2, tamanho, tamanho, 0, 0, tamanho, tamanho)
  canvas.toBlob((blob) => {
    if (!blob) return
    fotoPaciente.value = new File([blob], 'foto-paciente.jpg', { type: 'image/jpeg' })
    fecharCamera()
  }, 'image/jpeg', 0.9)
}

watch(() => paciente.cep, (valor) => {
  if (consultaCepTimer) clearTimeout(consultaCepTimer)
  const cep = valor.replace(/\D/g, '')
  const consulta = ++consultaCepAtual
  cepErro.value = ''
  cepBuscando.value = false
  if (cep.length === 8) consultaCepTimer = setTimeout(() => void buscarEnderecoPorCep(cep, consulta), 400)
})
watch(buscaTermoProcedimento, (termo) => {
  if (buscaProcedimentoTimer) clearTimeout(buscaProcedimentoTimer)
  buscaProcedimentoTimer = setTimeout(() => {
    void carregarProcedimentos(termo)
  }, 350)
})
watch(buscaTermoConvenio, (termo) => {
  if (buscaConvenioTimer) clearTimeout(buscaConvenioTimer)
  buscaConvenioTimer = setTimeout(() => {
    void carregarConvenios(termo)
  }, 350)
})
watch(() => auth.activeClinicaId, () => {
  aplicarUnidadeAtiva()
  void carregarMedicos()
})
watch(fotoPaciente, (foto) => {
  if (fotoPacienteUrl.value) URL.revokeObjectURL(fotoPacienteUrl.value)
  fotoPacienteUrl.value = foto ? URL.createObjectURL(foto) : null
})
watch(() => paciente.nomeCompleto, (nome) => {
  if (pacienteSelecionado.value && nome !== pacienteSelecionado.value.nome) iniciarPacienteNovo()
  if (buscaPacienteTimer) clearTimeout(buscaPacienteTimer)
  buscaPacienteTimer = setTimeout(() => {
    void buscarPacientesSpdata(nome)
  }, 350)
})
watch(cameraAberta, (aberta) => {
  if (!aberta) encerrarCamera()
})
onMounted(() => {
  void carregarOpcoesAtendimento()
})
onBeforeUnmount(() => {
  encerrarCamera()
  if (consultaCepTimer) clearTimeout(consultaCepTimer)
  if (buscaPacienteTimer) clearTimeout(buscaPacienteTimer)
  if (buscaProcedimentoTimer) clearTimeout(buscaProcedimentoTimer)
  if (buscaConvenioTimer) clearTimeout(buscaConvenioTimer)
  if (fotoPacienteUrl.value) URL.revokeObjectURL(fotoPacienteUrl.value)
})
</script>

<template>
  <div>
    <UHeader title="Novo atendimento">
      <template #right>
        <div class="flex items-center gap-2">
          <UBadge
            :label="userName"
            color="neutral"
            variant="soft"
          /><UColorModeButton />
        </div>
      </template>
    </UHeader>
    <div class="min-h-[calc(100vh-var(--ui-header-height))] bg-muted p-4 sm:p-6">
      <UTabs
        v-model="tabAtiva"
        :items="tabItems"
        color="primary"
        size="lg"
        variant="pill"
        :unmount-on-hide="false"
        :ui="{ list: 'bg-default/75 backdrop-blur border border-default', trigger: 'grow', content: 'pt-4' }"
      >
        <template #paciente>
          <UForm
            :state="paciente"
            class="space-y-4"
            @submit="proximoPaciente"
          >
            <CardCadastro
              titulo="Informações pessoais"
              cor="primary"
              icone="i-lucide-user"
              accordion
              aberto-inicialmente
            >
              <div class="grid gap-6 lg:grid-cols-[16.25rem_minmax(0,1fr)]">
                <UFileUpload
                  v-model="fotoPaciente"
                  icon="i-lucide-image"
                  label="Adicionar imagem do paciente"
                  layout="grid"
                  :interactive="false"
                  class="size-65"
                >
                  <template #actions="{ open }">
                    <UButton
                      label="Selecionar imagem"
                      icon="i-lucide-upload"
                      color="neutral"
                      variant="outline"
                      @click="open()"
                    /><UButton
                      label="Abrir câmera"
                      icon="i-lucide-camera"
                      color="neutral"
                      variant="outline"
                      @click="abrirCamera"
                    />
                  </template>
                </UFileUpload>
                <div class="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
                  <UFormField
                    label="Nome completo"
                    name="nomeCompleto"
                    required
                    class="sm:col-span-2 xl:col-span-3"
                  >
                    <UInputMenu
                      v-model="paciente.nomeCompleto"
                      mode="autocomplete"
                      :items="sugestoesPacientes"
                      value-key="label"
                      :filter-fields="['label', 'cpf', 'prontuario']"
                      placeholder="Digite ou pesquise por nome, CPF ou prontuário"
                      icon="i-lucide-search"
                      clear
                      class="w-full"
                    >
                      <template #item-label="{ item }">
                        <div>
                          <p>{{ item.label }}</p><p class="text-xs text-muted">
                            {{ item.cpf }} · {{ item.prontuario }}
                          </p>
                        </div>
                      </template>
                    </UInputMenu>
                  </UFormField>
                  <UFormField
                    label="CPF"
                    name="cpf"
                  >
                    <UInput
                      :model-value="paciente.cpf"
                      placeholder="000.000.000-00"
                      inputmode="numeric"
                      class="w-full"
                      @update:model-value="paciente.cpf = formatarCpf($event)"
                    />
                  </UFormField>
                  <UFormField
                    label="Data de nascimento"
                    name="dataNascimento"
                  >
                    <UInputDate
                      v-model="dataNascimento"
                      class="w-full"
                    />
                  </UFormField>
                  <UFormField
                    label="Nome social"
                    name="nomeSocial"
                    class="xl:col-span-2"
                  >
                    <UInput
                      v-model="paciente.nomeSocial"
                      class="w-full"
                    />
                  </UFormField>
                  <UFormField
                    label="Nome da mãe"
                    name="nomeMae"
                  >
                    <UInput
                      v-model="paciente.nomeMae"
                      class="w-full"
                    />
                  </UFormField>
                  <UFormField
                    label="RG"
                    name="rg"
                  >
                    <UInput
                      v-model="paciente.rg"
                      class="w-full"
                    />
                  </UFormField><UFormField
                    label="Órgão emissor"
                    name="orgaoEmissor"
                  >
                    <UInput
                      v-model="paciente.orgaoEmissor"
                      placeholder="Ex.: SSP"
                      class="w-full"
                    />
                  </UFormField>
                  <UFormField
                    label="Sexo biológico"
                    name="sexoBiologico"
                  >
                    <USelect
                      v-model="paciente.sexoBiologico"
                      :items="opcoesSexo"
                      placeholder="Selecione"
                      class="w-full"
                    />
                  </UFormField><UFormField
                    label="Identidade de gênero"
                    name="identidadeGenero"
                  >
                    <USelect
                      v-model="paciente.identidadeGenero"
                      :items="opcoesGenero"
                      placeholder="Selecione"
                      class="w-full"
                    />
                  </UFormField><UFormField
                    label="Estado civil"
                    name="estadoCivil"
                  >
                    <USelect
                      v-model="paciente.estadoCivil"
                      :items="opcoesEstadoCivil"
                      placeholder="Selecione"
                      class="w-full"
                    />
                  </UFormField>
                  <UFormField
                    label="Nacionalidade"
                    name="nacionalidade"
                  >
                    <UInput
                      v-model="paciente.nacionalidade"
                      class="w-full"
                    />
                  </UFormField><UFormField
                    label="Naturalidade"
                    name="naturalidade"
                    class="xl:col-span-2"
                  >
                    <UInput
                      v-model="paciente.naturalidade"
                      placeholder="Cidade/UF de nascimento"
                      class="w-full"
                    />
                  </UFormField>
                </div>
              </div>
            </CardCadastro>
            <CardCadastro
              titulo="Informações de contato"
              cor="tertiary"
              icone="i-lucide-phone"
            >
              <div class="grid grid-cols-1 gap-4 sm:grid-cols-3">
                <UFormField
                  label="Celular (WhatsApp)"
                  name="celularWhatsapp"
                >
                  <UInput
                    :model-value="paciente.celularWhatsapp"
                    inputmode="tel"
                    class="w-full"
                    @update:model-value="paciente.celularWhatsapp = formatarTelefone($event)"
                  />
                </UFormField><UFormField
                  label="Telefone fixo"
                  name="telefoneFixo"
                >
                  <UInput
                    :model-value="paciente.telefoneFixo"
                    inputmode="tel"
                    class="w-full"
                    @update:model-value="paciente.telefoneFixo = formatarTelefone($event)"
                  />
                </UFormField><UFormField
                  label="E-mail"
                  name="email"
                >
                  <UInput
                    v-model="paciente.email"
                    type="email"
                    class="w-full"
                  />
                </UFormField>
              </div>
            </CardCadastro>
            <CardCadastro
              titulo="Endereço"
              cor="quinary"
              icone="i-lucide-map-pin"
            >
              <div class="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
                <UFormField
                  label="CEP"
                  name="cep"
                  :description="cepErro || undefined"
                >
                  <UInput
                    :model-value="paciente.cep"
                    placeholder="00000-000"
                    inputmode="numeric"
                    :loading="cepBuscando"
                    class="w-full"
                    @update:model-value="paciente.cep = formatarCep($event)"
                  />
                </UFormField><UFormField
                  label="Endereço (logradouro)"
                  name="logradouro"
                  class="sm:col-span-2 xl:col-span-3"
                >
                  <UInput
                    v-model="paciente.logradouro"
                    class="w-full"
                  />
                </UFormField><UFormField
                  label="Número"
                  name="numero"
                >
                  <UInput
                    v-model="paciente.numero"
                    class="w-full"
                  />
                </UFormField><UFormField
                  label="Complemento"
                  name="complemento"
                >
                  <UInput
                    v-model="paciente.complemento"
                    class="w-full"
                  />
                </UFormField><UFormField
                  label="Bairro"
                  name="bairro"
                  class="sm:col-span-2"
                >
                  <UInput
                    v-model="paciente.bairro"
                    class="w-full"
                  />
                </UFormField><UFormField
                  label="Cidade"
                  name="cidade"
                  class="sm:col-span-2"
                >
                  <UInput
                    v-model="paciente.cidade"
                    class="w-full"
                  />
                </UFormField><UFormField
                  label="UF"
                  name="estadoUf"
                >
                  <USelect
                    v-model="paciente.estadoUf"
                    :items="estadosBr"
                    placeholder="Selecione"
                    class="w-full"
                  />
                </UFormField><UFormField
                  label="Código IBGE"
                  name="codigoIbge"
                >
                  <UInput
                    v-model="paciente.codigoIbge"
                    inputmode="numeric"
                    class="w-full"
                  />
                </UFormField>
              </div>
            </CardCadastro>
            <div class="flex justify-end">
              <UButton
                type="submit"
                label="Próximo"
                trailing-icon="i-lucide-arrow-right"
                size="lg"
                class="w-full sm:w-auto"
              />
            </div>
          </UForm>
        </template>
        <template #atendimento>
          <UForm
            :state="atendimento"
            class="space-y-4"
            @submit="proximoAtendimento"
          >
            <UCard>
              <div class="flex flex-col gap-4 sm:flex-row sm:items-center">
                <UAvatar
                  :src="fotoPacienteUrl || undefined"
                  :alt="paciente.nomeCompleto"
                  color="primary"
                  size="xl"
                />
                <div class="min-w-0 flex-1">
                  <p class="truncate text-lg font-semibold text-highlighted">
                    {{ paciente.nomeCompleto }}
                  </p>
                  <p class="text-sm text-muted">
                    Prontuário {{ prontuarioAtual }}
                  </p>
                  <div class="mt-3 grid grid-cols-2 gap-x-4 gap-y-2 text-sm sm:grid-cols-4">
                    <p><span class="text-muted">CPF:</span> {{ paciente.cpf || '-' }}</p>
                    <p><span class="text-muted">Sexo:</span> {{ paciente.sexoBiologico || '-' }}</p>
                    <p><span class="text-muted">Idade:</span> {{ idadePaciente || '-' }}</p>
                    <p><span class="text-muted">Cidade:</span> {{ paciente.cidade ? `${paciente.cidade}/${paciente.estadoUf}` : '-' }}</p>
                  </div>
                </div>
              </div>
            </UCard>
            <CardCadastro
              titulo="Dados do atendimento"
              cor="secondary"
              icone="i-lucide-stethoscope"
            >
              <div class="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
                <UFormField
                  label="Nº do registro"
                  name="registro"
                >
                  <UInput
                    v-model="atendimento.registro"
                    class="w-full"
                  />
                </UFormField><UFormField
                  label="Data de entrada"
                  name="dataEntrada"
                >
                  <UInputDate
                    v-model="dataEntrada"
                    class="w-full"
                  />
                </UFormField><UFormField
                  label="Hora"
                  name="horaEntrada"
                >
                  <UInputTime
                    v-model="horaEntrada"
                    class="w-full"
                  />
                </UFormField><UFormField
                  label="Caráter da solicitação"
                  name="caraterSolicitacao"
                >
                  <USelect
                    v-model="atendimento.caraterSolicitacao"
                    :items="opcoesCarater"
                    placeholder="Selecione"
                    class="w-full"
                  />
                </UFormField><UFormField
                  label="Cód. procedimento"
                  name="codigoProcedimento"
                >
                  <UInputMenu
                    v-model="atendimento.codigoProcedimento"
                    v-model:search-term="buscaTermoProcedimento"
                    :items="sugestoesProcedimentos"
                    :loading="carregandoProcedimentos"
                    label-key="label"
                    value-key="codigo"
                    :filter-fields="['label', 'codigo', 'codigoTuss', 'nome']"
                    mode="autocomplete"
                    placeholder="Busque por código ou nome"
                    icon="i-lucide-search"
                    clear
                    class="w-full"
                  />
                </UFormField><UFormField
                  label="Nome do procedimento"
                  name="nomeProcedimento"
                  class="sm:col-span-2"
                >
                  <UInputMenu
                    v-model="atendimento.nomeProcedimento"
                    v-model:search-term="buscaTermoProcedimento"
                    :items="sugestoesProcedimentos"
                    :loading="carregandoProcedimentos"
                    label-key="label"
                    value-key="nome"
                    :filter-fields="['label', 'codigo', 'codigoTuss', 'nome']"
                    mode="autocomplete"
                    placeholder="Busque o procedimento"
                    icon="i-lucide-search"
                    clear
                    class="w-full"
                  />
                </UFormField><UFormField
                  label="Tipo"
                  name="tipoProcedimento"
                >
                  <USelect
                    v-model="atendimento.tipoProcedimento"
                    :items="opcoesTipo"
                    placeholder="Selecione"
                    class="w-full"
                  />
                </UFormField><UFormField
                  label="Modalidade"
                  name="modalidade"
                >
                  <USelect
                    v-model="atendimento.modalidade"
                    :items="opcoesModalidade"
                    placeholder="Selecione"
                    class="w-full"
                  />
                </UFormField><UFormField
                  name="ehRetorno"
                  class="flex items-end"
                >
                  <USwitch
                    v-model="atendimento.ehRetorno"
                    label="É retorno?"
                  />
                </UFormField><UFormField
                  name="recemNascido"
                  class="flex items-end"
                >
                  <USwitch
                    v-model="atendimento.recemNascido"
                    label="Recém-nascido?"
                  />
                </UFormField><UFormField
                  name="atualizaFaturamento"
                  class="flex items-end"
                >
                  <USwitch
                    v-model="atendimento.atualizaFaturamento"
                    label="Atualiza faturamento"
                  />
                </UFormField>
              </div>
            </CardCadastro>
            <CardCadastro
              titulo="Convênio e plano"
              cor="tertiary"
              icone="i-lucide-credit-card"
            >
              <div class="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
                <UFormField
                  label="Convênio (número)"
                  name="numeroConvenio"
                >
                  <UInputMenu
                    v-model="atendimento.numeroConvenio"
                    v-model:search-term="buscaTermoConvenio"
                    :items="sugestoesConvenios"
                    :loading="carregandoConvenios"
                    label-key="label"
                    value-key="codigo"
                    :filter-fields="['label', 'codigo', 'registroAns']"
                    mode="autocomplete"
                    placeholder="Busque por número ou nome"
                    icon="i-lucide-search"
                    clear
                    class="w-full"
                  />
                </UFormField><UFormField
                  label="Descrição"
                  name="descricaoConvenio"
                  class="sm:col-span-2"
                >
                  <UInputMenu
                    v-model="atendimento.descricaoConvenio"
                    v-model:search-term="buscaTermoConvenio"
                    :items="sugestoesConvenios"
                    :loading="carregandoConvenios"
                    label-key="label"
                    value-key="label"
                    :filter-fields="['label', 'codigo', 'registroAns']"
                    mode="autocomplete"
                    placeholder="Preenchida pelo número do convênio"
                    icon="i-lucide-search"
                    clear
                    class="w-full"
                  />
                </UFormField><UFormField
                  label="Matrícula"
                  name="matricula"
                >
                  <UInput
                    v-model="atendimento.matricula"
                    class="w-full"
                  />
                </UFormField><UFormField
                  label="Validade"
                  name="validade"
                >
                  <UInput
                    v-model="atendimento.validade"
                    placeholder="MM/AAAA"
                    class="w-full"
                  />
                </UFormField><UFormField
                  label="Guia de autorização"
                  name="guiaAutorizacao"
                  class="sm:col-span-2 xl:col-span-3"
                >
                  <UInput
                    v-model="atendimento.guiaAutorizacao"
                    class="w-full"
                  />
                </UFormField>
              </div>
            </CardCadastro>
            <CardCadastro
              titulo="Médico & unidade"
              cor="quinary"
              icone="i-lucide-building-2"
            >
              <div class="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-5">
                <UFormField
                  label="CRM"
                  name="crm"
                >
                  <UInputMenu
                    v-model="atendimento.crm"
                    :items="sugestoesMedicos"
                    :loading="carregandoMedicos"
                    label-key="label"
                    value-key="crm"
                    :filter-fields="['label', 'crm', 'especialidade']"
                    mode="autocomplete"
                    placeholder="Busque por CRM ou médico"
                    icon="i-lucide-search"
                    clear
                    class="w-full"
                  />
                </UFormField><UFormField
                  label="Nome do médico"
                  name="nomeMedico"
                  class="sm:col-span-2"
                >
                  <UInputMenu
                    v-model="atendimento.nomeMedico"
                    :items="sugestoesMedicos"
                    :loading="carregandoMedicos"
                    label-key="label"
                    value-key="label"
                    :filter-fields="['label', 'crm', 'especialidade']"
                    mode="autocomplete"
                    placeholder="Busque o médico"
                    icon="i-lucide-search"
                    clear
                    class="w-full"
                  />
                </UFormField><UFormField
                  label="Especialidade"
                  name="especialidade"
                >
                  <UInput
                    v-model="atendimento.especialidade"
                    class="w-full"
                  />
                </UFormField><UFormField
                  label="C.D.C. número"
                  name="centroCustoNumero"
                >
                  <UInputMenu
                    v-model="atendimento.centroCustoNumero"
                    :items="sugestoesUnidades"
                    label-key="label"
                    value-key="codigo"
                    :filter-fields="['label', 'codigo']"
                    mode="autocomplete"
                    placeholder="Busque por CDC ou unidade"
                    icon="i-lucide-search"
                    clear
                    class="w-full"
                  />
                </UFormField><UFormField
                  label="C.D.C. nome"
                  name="centroCustoNome"
                >
                  <UInputMenu
                    v-model="atendimento.centroCustoNome"
                    :items="sugestoesUnidades"
                    label-key="label"
                    value-key="label"
                    :filter-fields="['label', 'codigo']"
                    mode="autocomplete"
                    placeholder="Busque a unidade"
                    icon="i-lucide-search"
                    clear
                    class="w-full"
                  />
                </UFormField><UFormField
                  label="Unidade"
                  name="unidade"
                  class="sm:col-span-2"
                >
                  <UInputMenu
                    v-model="atendimento.unidade"
                    :items="sugestoesUnidades"
                    label-key="label"
                    value-key="label"
                    :filter-fields="['label', 'codigo']"
                    mode="autocomplete"
                    placeholder="Busque a unidade"
                    icon="i-lucide-search"
                    clear
                    class="w-full"
                  />
                </UFormField>
              </div>
            </CardCadastro>
            <div class="flex flex-col-reverse gap-2 sm:flex-row sm:justify-between">
              <UButton
                label="Voltar"
                color="neutral"
                variant="outline"
                icon="i-lucide-arrow-left"
                @click="void (tabAtiva = 'paciente')"
              /><UButton
                type="submit"
                label="Próximo"
                trailing-icon="i-lucide-arrow-right"
              />
            </div>
          </UForm>
        </template>
        <template #responsavel>
          <UForm
            :state="responsavel"
            class="space-y-4"
            @submit="finalizarCadastro"
          >
            <CardCadastro
              titulo="Responsável pelo paciente"
              cor="quaternary"
              icone="i-lucide-users"
              accordion
              aberto-inicialmente
            >
              <div class="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
                <UFormField
                  label="Nome do responsável"
                  name="nome"
                  class="sm:col-span-2"
                >
                  <UInput
                    v-model="responsavel.nome"
                    class="w-full"
                  />
                </UFormField><UFormField
                  label="Identidade"
                  name="identidade"
                >
                  <UInput
                    v-model="responsavel.identidade"
                    class="w-full"
                  />
                </UFormField><UFormField
                  label="CPF"
                  name="cpf"
                >
                  <UInput
                    :model-value="responsavel.cpf"
                    inputmode="numeric"
                    class="w-full"
                    @update:model-value="responsavel.cpf = formatarCpf($event)"
                  />
                </UFormField><UFormField
                  label="CNPJ"
                  name="cnpj"
                >
                  <UInput
                    :model-value="responsavel.cnpj"
                    inputmode="numeric"
                    class="w-full"
                    @update:model-value="responsavel.cnpj = formatarCpfCnpj($event)"
                  />
                </UFormField><UFormField
                  label="Data de nascimento"
                  name="dataNascimento"
                >
                  <UInputDate
                    v-model="dataNascimentoResponsavel"
                    class="w-full"
                  />
                </UFormField><UFormField
                  label="Parentesco"
                  name="parentesco"
                >
                  <UInput
                    v-model="responsavel.parentesco"
                    class="w-full"
                  />
                </UFormField><UFormField
                  label="Profissão"
                  name="profissao"
                >
                  <UInput
                    v-model="responsavel.profissao"
                    class="w-full"
                  />
                </UFormField><UFormField
                  label="CEP"
                  name="cep"
                >
                  <UInput
                    :model-value="responsavel.cep"
                    inputmode="numeric"
                    class="w-full"
                    @update:model-value="responsavel.cep = formatarCep($event)"
                  />
                </UFormField><UFormField
                  label="Endereço"
                  name="logradouro"
                  class="sm:col-span-2 xl:col-span-3"
                >
                  <UInput
                    v-model="responsavel.logradouro"
                    class="w-full"
                  />
                </UFormField><UFormField
                  label="Número"
                  name="numero"
                >
                  <UInput
                    v-model="responsavel.numero"
                    class="w-full"
                  />
                </UFormField><UFormField
                  label="Complemento"
                  name="complemento"
                >
                  <UInput
                    v-model="responsavel.complemento"
                    class="w-full"
                  />
                </UFormField><UFormField
                  label="Bairro"
                  name="bairro"
                  class="sm:col-span-2"
                >
                  <UInput
                    v-model="responsavel.bairro"
                    class="w-full"
                  />
                </UFormField><UFormField
                  label="Cidade"
                  name="cidade"
                  class="sm:col-span-2"
                >
                  <UInput
                    v-model="responsavel.cidade"
                    class="w-full"
                  />
                </UFormField><UFormField
                  label="UF"
                  name="uf"
                >
                  <USelect
                    v-model="responsavel.uf"
                    :items="estadosBr"
                    placeholder="Selecione"
                    class="w-full"
                  />
                </UFormField><UFormField
                  label="Telefone"
                  name="telefone"
                >
                  <UInput
                    :model-value="responsavel.telefone"
                    inputmode="tel"
                    class="w-full"
                    @update:model-value="responsavel.telefone = formatarTelefone($event)"
                  />
                </UFormField>
              </div>
            </CardCadastro>
            <div class="flex flex-col-reverse gap-2 sm:flex-row sm:justify-between">
              <UButton
                label="Voltar"
                color="neutral"
                variant="outline"
                icon="i-lucide-arrow-left"
                @click="void (tabAtiva = 'atendimento')"
              /><UButton
                type="submit"
                label="Finalizar cadastro"
                icon="i-lucide-circle-check"
              />
            </div>
          </UForm>
        </template>
      </UTabs>
    </div>
    <UModal
      v-model:open="cameraAberta"
      title="Capturar foto do paciente"
      description="Posicione o rosto do paciente na área da câmera."
    >
      <template #body>
        <div class="space-y-4">
          <div class="aspect-square overflow-hidden rounded-lg bg-elevated">
            <video
              v-if="!cameraErro"
              ref="videoCamera"
              autoplay
              muted
              playsinline
              class="size-full object-cover"
            /><div
              v-else
              class="flex size-full items-center justify-center p-6 text-center text-sm text-error"
            >
              {{ cameraErro }}
            </div>
          </div><p
            v-if="cameraCarregando"
            class="text-sm text-muted"
          >
            Iniciando câmera...
          </p>
        </div>
      </template><template #footer>
        <UButton
          label="Cancelar"
          color="neutral"
          variant="outline"
          @click="fecharCamera"
        /><UButton
          label="Capturar foto"
          icon="i-lucide-camera"
          :disabled="cameraCarregando || Boolean(cameraErro)"
          @click="capturarFoto"
        />
      </template>
    </UModal>
  </div>
</template>
