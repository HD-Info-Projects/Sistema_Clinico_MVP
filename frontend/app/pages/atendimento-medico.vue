<script setup lang="ts">
import type {
  DocumentoMedico,
  DocumentoMedicoTipo,
  ExameCatalogo,
  ExameSelecionado,
  HistoricoLocalRecord,
  PadraoAnamnese,
  PadraoExame,
  PadraoReceita
} from '~/types'
import { usePdfMake } from '~/utils/pdf'
import { buildSolicitacaoExames, buildReceita, buildReceitaEspecialDupla, buildAtestadoComparecimento } from '~/utils/pdf-documents'
import { gerarHtmlGuiaTiss, imprimirGuiaTiss } from '~/utils/guia-tiss'

const auth = useAuthStore()
const agendamentosStore = useAgendamentosStore()
const padroesStore = usePadroesStore()
const padroesAnamneseStore = usePadroesAnamneseStore()
const padroesOrientacoesStore = usePadroesOrientacoesStore()
const cronometro = useCronometroStore()
const toast = useToast()
onMounted(() => {
  padroesStore.fetchAll()
  padroesAnamneseStore.fetchAll()
  padroesOrientacoesStore.fetchAll()
  cronometro.start()
})

onBeforeRouteLeave(() => {
  salvarDraftAgora()
  if (cronometro.isRunning) cronometro.pause()
})

const agendamento = computed(() => agendamentosStore.emAtendimento)
const route = useRoute()

const modoEdicao = computed(() => {
  const id = Number(route.query.id)
  return Number.isInteger(id) && id > 0 ? id : null
})

async function carregarConsultaExistente() {
  const ag = agendamento.value
  const edicaoId = modoEdicao.value
  if (!ag || !edicaoId || ag.id !== edicaoId) return
  if (!import.meta.client) return

  try {
    const registros = await $fetch<HistoricoLocalRecord[]>(
      `/api/historico-local/${ag.paciente.id}`,
      {
        query: { spdataAtendimentoId: ag.spdataAtendimentoId ?? undefined }
      }
    )
    const registro = registros?.[0]
    if (!registro) return

    anamneseTexto.value = registro.anamnese ?? ''

    const cids: CidResultado[] = []
    if (registro.cid_principal) {
      cids.push({
        cid: registro.cid_principal,
        nome: registro.cid_principal_descricao ?? ''
      })
    }
    for (const s of registro.cids_secundarios ?? []) {
      if (s?.codigo) cids.push({ cid: s.codigo, nome: s.descricao ?? '' })
    }
    cidSelecionadoLista.value = cids

    receitaTexto.value = (registro.medicamentos ?? []).join('\n')

    examesSelecionados.value = (registro.exames ?? [])
      .map(e => normalizarExameSelecionado(e))
      .filter((e): e is ExameSelecionado => e !== null)
  } catch (error) {
    console.error('Erro ao carregar consulta para edição', error)
  }
}
const documentosMedicos = shallowRef<Partial<Record<DocumentoMedicoTipo, DocumentoMedico>>>({})
let documentosMedicosRequestId = 0

function documentoMedico(tipo: DocumentoMedicoTipo) {
  return documentosMedicos.value[tipo] ?? null
}

const documentoAtestado = computed(() => documentoMedico('ATESTADO'))
const documentoEncaminhamento = computed(() => documentoMedico('ENCAMINHAMENTO'))
const documentoProcedimento = computed(() => documentoMedico('SOLICITACAO_PROCEDIMENTO'))
const documentoOpme = computed(() => documentoMedico('SOLICITACAO_OPME'))

function atualizarDocumentoMedico(documento: DocumentoMedico) {
  documentosMedicos.value = {
    ...documentosMedicos.value,
    [documento.tipoDocumento]: documento
  }
}

async function carregarDocumentosMedicosDoAtendimento() {
  const requestId = ++documentosMedicosRequestId
  const ag = agendamento.value

  if (!ag) {
    documentosMedicos.value = {}
    return
  }

  try {
    const documentos = await $fetch<DocumentoMedico[]>(`/api/documentos-medicos/${ag.id}`)

    if (requestId !== documentosMedicosRequestId) return

    const porTipo: Partial<Record<DocumentoMedicoTipo, DocumentoMedico>> = {}
    for (const documento of documentos) {
      porTipo[documento.tipoDocumento] = documento
    }

    documentosMedicos.value = porTipo
  } catch {
    if (requestId === documentosMedicosRequestId) documentosMedicos.value = {}
    console.error('Erro ao carregar documentos médicos')
  }
}

watch(
  () => agendamento.value?.id,
  () => {
    if (import.meta.client) void carregarDocumentosMedicosDoAtendimento()
  },
  { immediate: true }
)

const exame = ref<ExameSelecionado | null>(null)

const tabAtiva = ref('0')
const tabItems = [
  { label: 'Anamnese e Evolução', icon: 'i-lucide-notebook-text' },
  { label: 'Solicitar Exames', icon: 'i-lucide-flask-conical' },
  { label: 'Receita', icon: 'i-lucide-pill' },
  { label: 'Conclusão', icon: 'i-lucide-check-circle' }
]

type CidResultado = { cid: string, nome: string }

type AtendimentoDraft = {
  version: 5
  savedAt: string
  agendamentoId: number
  pacienteId: number | null
  tabAtiva: string
  anamneseTexto: string
  cidSelecionadoLista: CidResultado[]
  cidPrincipalIndex: number
  searchCid: string
  receitaTexto: string
  remedioNome: string
  remedioDosagem: string
  remedioDetalhes: string
  examesSelecionados: ExameSelecionado[]
  exameSelecionado: ExameCatalogo | null
  buscaTermoExame: string
  caraterAtendimento: boolean
}

type AtendimentoDraftSalvo = Partial<Omit<AtendimentoDraft, 'version'>> & {
  version?: number
  savedAt: string
  cidSelecionado?: CidResultado | null
}

let buscaTimeout: ReturnType<typeof setTimeout> | null = null
let cidController: AbortController | null = null
let cidRequestId = 0

const searchCid = ref('')
const resultadosCid = ref<CidResultado[]>([])
const cidSelecionadoLista = ref<CidResultado[]>([])
const cidTempSelecionado = ref<CidResultado | null>(null)
const cidPrincipalIndex = ref(0)
const isLoadingCid = ref(false)
const erroBuscaCid = ref('')

watch(searchCid, (val) => {
  onSearchInput(val)
})

const CID_CODE_PATTERN = /^[A-Za-z][0-9.]*$/

function podeBuscarCid(q: string) {
  const termo = q.trim()

  if (!termo) return false

  if (CID_CODE_PATTERN.test(termo)) {
    return termo.length >= 2
  }

  return termo.length >= 3
}

function limparResultadosCid() {
  cidRequestId++
  cidController?.abort()
  resultadosCid.value = []
  erroBuscaCid.value = ''
  isLoadingCid.value = false
}

function mensagemErroFetch(error: unknown, fallback: string) {
  const fetchError = error as {
    data?: { error?: string, message?: string, statusMessage?: string }
    response?: { _data?: { error?: string, message?: string, statusMessage?: string } }
    message?: string
  }
  const data = fetchError.response?._data ?? fetchError.data

  return data?.error
    || data?.message
    || data?.statusMessage
    || fetchError.message
    || fallback
}

async function buscarCid(q: string) {
  const termo = q.trim()

  if (!podeBuscarCid(termo)) {
    limparResultadosCid()
    return
  }

  const requestId = ++cidRequestId

  cidController?.abort()
  cidController = new AbortController()

  isLoadingCid.value = true
  erroBuscaCid.value = ''

  try {
    const data = await $fetch<CidResultado[]>('/api/cid', {
      query: {
        q: termo,
        limit: 20
      },
      signal: cidController.signal
    })

    if (requestId !== cidRequestId) return
    if (searchCid.value.trim() !== termo) return

    resultadosCid.value = data
  } catch (error) {
    const name = error instanceof Error ? error.name : ''

    if (name === 'AbortError') return
    if (requestId !== cidRequestId) return

    resultadosCid.value = []
    erroBuscaCid.value = mensagemErroFetch(error, 'Não foi possível buscar CID no momento.')
  } finally {
    if (requestId === cidRequestId) isLoadingCid.value = false
  }
}

function onSearchInput(val: string) {
  if (buscaTimeout) clearTimeout(buscaTimeout)

  if (!podeBuscarCid(val)) {
    limparResultadosCid()
    return
  }

  buscaTimeout = setTimeout(() => {
    buscarCid(val)
  }, 300)
}

function removerCid(index: number) {
  cidSelecionadoLista.value.splice(index, 1)
  if (cidPrincipalIndex.value >= cidSelecionadoLista.value.length) {
    cidPrincipalIndex.value = Math.max(0, cidSelecionadoLista.value.length - 1)
  }
}

function adicionarCid(item: CidResultado) {
  const jaExiste = cidSelecionadoLista.value.some(c => c.cid === item.cid)
  if (jaExiste) return
  cidSelecionadoLista.value.push(item)
  searchCid.value = ''
  resultadosCid.value = []
}

const anamneseTexto = ref('')
const padraoAnamneseSelected = ref<{ label: string, value: PadraoAnamnese }>()

function adicionarPadraoAnamnese() {
  if (!padraoAnamneseSelected.value) return
  anamneseTexto.value += padraoAnamneseSelected.value.value.conteudo
  padraoAnamneseSelected.value = undefined
}

const receitaTexto = ref('')
const remedioNome = ref('')
const remedioDosagem = ref('')
const remedioDetalhes = ref('')
const padraoReceitaSelected = ref<{ label: string, value: PadraoReceita }>()

function adicionarRemedio() {
  if (!remedioNome.value && !remedioDosagem.value) return
  receitaTexto.value += `\n• ${remedioNome.value}${remedioDosagem.value ? ` — ${remedioDosagem.value}` : ''}${remedioDetalhes.value ? ` — ${remedioDetalhes.value}` : ''}\n`
  remedioNome.value = ''
  remedioDosagem.value = ''
  remedioDetalhes.value = ''
}

function adicionarPadraoReceita() {
  if (!padraoReceitaSelected.value) return
  for (const m of padraoReceitaSelected.value.value.medicamentos) {
    receitaTexto.value += `\n• ${m.nome} — ${m.dosagem}${m.detalhes ? ` — ${m.detalhes}` : ''}\n`
  }
  padraoReceitaSelected.value = undefined
}

const examesSelecionados = ref<ExameSelecionado[]>([])
const exameSelecionado = ref<ExameCatalogo | null>(null)
const buscaTermoExame = ref('')
const sugestoesExames = ref<ExameCatalogo[]>([])
const carregandoExames = ref(false)
const erroBuscaExames = ref('')
const exameTemplateSelected = ref<{ label: string, value: PadraoExame }>()
const caraterAtendimento = ref(false)

const cidPrincipal = computed(() => {
  if (cidSelecionadoLista.value.length === 0) return ''
  const idx = cidPrincipalIndex.value
  const cid = cidSelecionadoLista.value[idx]
  return cid ? `${cid.cid} - ${cid.nome}` : ''
})

let buscaExameTimeout: ReturnType<typeof setTimeout> | null = null
let examesController: AbortController | null = null
let examesRequestId = 0

watch(exameSelecionado, (val) => {
  if (val) adicionarExame(val)
})

watch(buscaTermoExame, (val) => {
  if (buscaExameTimeout) clearTimeout(buscaExameTimeout)

  const termo = val.trim()

  if (termo.length < 2) {
    limparSugestoesExames()
    return
  }

  buscaExameTimeout = setTimeout(() => {
    buscarExames(termo)
  }, 300)
})

function limparSugestoesExames() {
  examesRequestId++
  examesController?.abort()
  sugestoesExames.value = []
  erroBuscaExames.value = ''
  carregandoExames.value = false
}

async function buscarExames(q: string) {
  const termo = q.trim()
  if (termo.length < 2) return

  const requestId = ++examesRequestId
  examesController?.abort()
  examesController = new AbortController()

  carregandoExames.value = true
  erroBuscaExames.value = ''
  try {
    const data = await $fetch<{ exames: ExameCatalogo[] }>('/api/exames/buscar', {
      query: { q: termo },
      signal: examesController.signal
    })

    if (requestId !== examesRequestId) return
    if (buscaTermoExame.value.trim() !== termo) return

    sugestoesExames.value = data.exames || []
  } catch (error) {
    if (error instanceof Error && error.name === 'AbortError') return
    if (requestId !== examesRequestId) return
    sugestoesExames.value = []
    erroBuscaExames.value = mensagemErroFetch(error, 'Não foi possível buscar exames no momento.')
  } finally {
    if (requestId === examesRequestId) carregandoExames.value = false
  }
}

function normalizarIdExame(valor: unknown) {
  if (valor === null || valor === undefined || valor === '') return null

  const numero = Number(valor)
  return Number.isInteger(numero) && numero > 0 ? numero : null
}

function normalizarExameSelecionado(valor: unknown): ExameSelecionado | null {
  if (typeof valor === 'string') {
    const nome = valor.trim()
    return nome ? { nome, exameId: null, codigo_amb: null, codigo_alfanumerico: null } : null
  }

  if (!valor || typeof valor !== 'object') return null

  const item = valor as Record<string, unknown>
  const nome = typeof item.nome === 'string' ? item.nome.trim() : ''
  const exameId = normalizarIdExame(item.exameId ?? item.exame_id ?? item.id)
  const codigo_amb = typeof item.codigo_amb === 'string' ? item.codigo_amb : null
  const codigo_alfanumerico = typeof item.codigo_alfanumerico === 'string' ? item.codigo_alfanumerico : null
  const orientacao = typeof (item.orientacao ?? item.orientacoes) === 'string'
    ? String(item.orientacao ?? item.orientacoes)
    : null

  if (!nome) return null

  return {
    nome,
    exameId,
    codigo_amb,
    codigo_alfanumerico,
    orientacao: htmlTemConteudo(orientacao) ? orientacao : null
  }
}

function htmlTemConteudo(valor?: string | null) {
  const texto = (valor || '')
    .replace(/<[^>]*>/g, ' ')
    .replace(/&nbsp;|&#160;|&#xA0;/gi, ' ')
    .replace(/[\u00A0\u200B-\u200D\uFEFF]/g, '')
    .trim()

  return Boolean(texto)
}

function exameExisteNaLista(lista: ExameSelecionado[], exame: ExameSelecionado) {
  const nome = exame.nome.trim().toLocaleLowerCase('pt-BR')

  return lista.some((atual) => {
    if (atual.exameId && exame.exameId && atual.exameId === exame.exameId) return true
    return atual.nome.trim().toLocaleLowerCase('pt-BR') === nome
  })
}

function normalizarListaExames(valor: unknown) {
  if (!Array.isArray(valor)) return []

  const exames: ExameSelecionado[] = []
  for (const item of valor) {
    const exame = normalizarExameSelecionado(item)
    if (!exame || exameExisteNaLista(exames, exame)) continue
    exames.push(exame)
  }

  return exames
}

function adicionarExame(valor: unknown) {
  const exame = normalizarExameSelecionado(valor)
  if (!exame) return
  if (exameExisteNaLista(examesSelecionados.value, exame)) return

  examesSelecionados.value.push(exame)
  exameSelecionado.value = null
  buscaTermoExame.value = ''
  limparSugestoesExames()
}

function adicionarOrientacao(valor: ExameSelecionado) {
  exame.value = valor
  showOrientacaoExamesModal.value = true
}

function exameTemOrientacao(valor: ExameSelecionado) {
  return htmlTemConteudo(valor.orientacao)
}

function salvarOrientacaoExame(orientacao: string) {
  if (!exame.value) return

  const selecionado = exame.value
  const index = examesSelecionados.value.findIndex((e) => {
    if (e === selecionado) return true
    if (e.exameId && selecionado.exameId && e.exameId === selecionado.exameId) return true
    return e.nome.trim().toLocaleLowerCase('pt-BR') === selecionado.nome.trim().toLocaleLowerCase('pt-BR')
  })
  if (index === -1) return

  examesSelecionados.value[index] = {
    ...examesSelecionados.value[index]!,
    orientacao: htmlTemConteudo(orientacao) ? orientacao.trim() : null
  }
  exame.value = examesSelecionados.value[index] ?? null
}

function adicionarExameManual() {
  adicionarExame(buscaTermoExame.value)
}

function removerExameDaLista(i: number) {
  examesSelecionados.value.splice(i, 1)
}

function adicionarPadraoExame() {
  if (!exameTemplateSelected.value) return
  for (const e of exameTemplateSelected.value.value.exames) {
    adicionarExame(e)
  }
  exameTemplateSelected.value = undefined
}

const showAtestadoModal = ref(false)
const showEncaminhamentoModal = ref(false)
const showProcedimentoModal = ref(false)
const showOpmeModal = ref(false)
const showOrientacaoExamesModal = ref(false)
const finalizandoConsulta = ref(false)
const draftSalvoEm = ref<string | null>(null)
const draftRestaurado = ref(false)

let draftTimer: ReturnType<typeof setTimeout> | null = null
let restaurandoDraft = false
let draftDesativado = false

const DRAFT_TTL_MS = 7 * 24 * 60 * 60 * 1000
const DRAFT_STORAGE_PREFIX = 'medsystem:atendimento-draft:'

const draftKey = computed(() => {
  const ag = agendamento.value
  if (!ag) return null

  return `${DRAFT_STORAGE_PREFIX}${ag.id}:${ag.paciente.id}`
})

function draftStorage() {
  return sessionStorage
}

const draftSalvoHorario = computed(() => {
  if (!draftSalvoEm.value) return ''

  return new Date(draftSalvoEm.value).toLocaleTimeString('pt-BR', {
    hour: '2-digit',
    minute: '2-digit'
  })
})

function montarDraft(): AtendimentoDraft | null {
  const ag = agendamento.value
  if (!ag) return null

  return {
    version: 5,
    savedAt: new Date().toISOString(),
    agendamentoId: ag.id,
    pacienteId: ag.paciente.id ?? null,
    tabAtiva: tabAtiva.value,
    anamneseTexto: anamneseTexto.value,
    cidSelecionadoLista: cidSelecionadoLista.value,
    cidPrincipalIndex: cidPrincipalIndex.value,
    searchCid: searchCid.value,
    receitaTexto: receitaTexto.value,
    remedioNome: remedioNome.value,
    remedioDosagem: remedioDosagem.value,
    remedioDetalhes: remedioDetalhes.value,
    examesSelecionados: [...examesSelecionados.value],
    exameSelecionado: exameSelecionado.value,
    buscaTermoExame: buscaTermoExame.value,
    caraterAtendimento: caraterAtendimento.value
  }
}

function draftTemConteudo(draft: AtendimentoDraft) {
  return Boolean(
    draft.anamneseTexto.trim()
    || draft.cidSelecionadoLista?.length
    || draft.searchCid.trim()
    || draft.receitaTexto.trim()
    || draft.remedioNome.trim()
    || draft.remedioDosagem.trim()
    || draft.remedioDetalhes.trim()
    || draft.examesSelecionados.length
    || Boolean(draft.exameSelecionado)
    || draft.buscaTermoExame.trim()
  )
}

function salvarDraftAgora() {
  if (!import.meta.client || !draftKey.value || draftDesativado) return

  const draft = montarDraft()
  if (!draft) return

  if (!draftTemConteudo(draft)) {
    draftStorage().removeItem(draftKey.value)
    localStorage.removeItem(draftKey.value)
    draftSalvoEm.value = null
    draftRestaurado.value = false
    return
  }

  draftStorage().setItem(draftKey.value, JSON.stringify(draft))
  localStorage.removeItem(draftKey.value)
  draftSalvoEm.value = draft.savedAt
}

function salvarDraftComDebounce() {
  if (restaurandoDraft) return
  if (draftTimer) clearTimeout(draftTimer)

  draftTimer = setTimeout(() => {
    salvarDraftAgora()
  }, 700)
}

function restaurarDraft() {
  if (!import.meta.client || !draftKey.value) return

  localStorage.removeItem(draftKey.value)

  const raw = draftStorage().getItem(draftKey.value)
  if (!raw) return

  try {
    const draft = JSON.parse(raw) as AtendimentoDraftSalvo
    const savedAt = new Date(draft.savedAt).getTime()

    if (!savedAt || Date.now() - savedAt > DRAFT_TTL_MS) {
      draftStorage().removeItem(draftKey.value)
      return
    }

    restaurandoDraft = true

    tabAtiva.value = draft.tabAtiva || '0'
    anamneseTexto.value = draft.anamneseTexto || ''
    if (draft.version === 1) {
      const old = draft.cidSelecionado
      cidSelecionadoLista.value = old ? [old] : []
      cidPrincipalIndex.value = 0
    } else {
      cidSelecionadoLista.value = draft.cidSelecionadoLista || []
      cidPrincipalIndex.value = draft.cidPrincipalIndex ?? 0
    }
    searchCid.value = draft.searchCid || ''
    receitaTexto.value = draft.receitaTexto || ''
    remedioNome.value = draft.remedioNome || ''
    remedioDosagem.value = draft.remedioDosagem || ''
    remedioDetalhes.value = draft.remedioDetalhes || ''
    examesSelecionados.value = normalizarListaExames(draft.examesSelecionados)
    exameSelecionado.value = null
    buscaTermoExame.value = draft.buscaTermoExame || ''
    caraterAtendimento.value = draft.caraterAtendimento ?? false
    draftSalvoEm.value = draft.savedAt
    draftRestaurado.value = true
  } catch {
    draftStorage().removeItem(draftKey.value)
  } finally {
    setTimeout(() => {
      restaurandoDraft = false
    }, 0)
  }
}

function limparDraft() {
  if (!import.meta.client || !draftKey.value) return

  draftDesativado = true
  draftStorage().removeItem(draftKey.value)
  localStorage.removeItem(draftKey.value)
  draftSalvoEm.value = null
  draftRestaurado.value = false
}

watch(
  [
    tabAtiva,
    anamneseTexto,
    cidSelecionadoLista,
    searchCid,
    receitaTexto,
    remedioNome,
    remedioDosagem,
    remedioDetalhes,
    examesSelecionados,
    exameSelecionado,
    buscaTermoExame,
    caraterAtendimento
  ],
  () => {
    salvarDraftComDebounce()
  },
  { deep: true }
)

watch(
  draftKey,
  (key) => {
    if (!key) return

    if (modoEdicao.value) {
      draftDesativado = true
      draftStorage().removeItem(key)
      localStorage.removeItem(key)
      draftSalvoEm.value = null
      draftRestaurado.value = false
      return
    }

    draftDesativado = false
    restaurarDraft()
  },
  { immediate: true }
)

watch(
  () => [modoEdicao.value, agendamento.value?.id] as const,
  ([edicaoId, agendamentoId]) => {
    if (edicaoId && edicaoId === agendamentoId && import.meta.client) {
      void carregarConsultaExistente()
    }
  },
  { immediate: true }
)

onMounted(() => {
  window.addEventListener('beforeunload', salvarDraftAgora)
})

onUnmounted(() => {
  window.removeEventListener('beforeunload', salvarDraftAgora)

  if (draftTimer) {
    clearTimeout(draftTimer)
    salvarDraftAgora()
  }
})

async function gerarReceitaPdf() {
  if (!receitaTexto.value.trim()) return
  const pdfMake = await usePdfMake()
  const doc = await buildReceita({
    paciente: agendamento.value?.paciente.nome ?? 'Paciente',
    data: new Date().toLocaleDateString('pt-BR'),
    medicamentos: [],
    texto: receitaTexto.value,
    medico: auth.user?.nome,
    crm: auth.user?.crm,
    especialidade: auth.user?.especialidades?.join(', ')
  })
  pdfMake.createPdf(doc).open()
}

async function gerarReceitaEspecialPdf() {
  if (!receitaTexto.value.trim()) return
  const pdfMake = await usePdfMake()
  const doc = await buildReceitaEspecialDupla({
    paciente: agendamento.value?.paciente.nome ?? 'Paciente',
    data: new Date().toLocaleDateString('pt-BR'),
    medicamentos: [],
    texto: receitaTexto.value,
    medico: auth.user?.nome,
    crm: auth.user?.crm,
    especialidade: auth.user?.especialidades?.join(', ')
  })
  pdfMake.createPdf(doc).open()
}

async function gerarSolicitacaoExames() {
  if (!examesSelecionados.value.length) return

  const convenio = (agendamento.value?.paciente.convenio ?? '').toLowerCase()

  if (convenio && convenio !== 'particular') {
    const params = {
      paciente: agendamento.value?.paciente.nome ?? 'Paciente',
      nomeSocial: agendamento.value?.paciente.nomeSocial,
      cpf: agendamento.value?.paciente.cpf,
      convenio: agendamento.value?.paciente.convenio ?? '',
      idConvenioSpdata: agendamento.value?.paciente.idConvenioSpdata,
      data: new Date().toLocaleDateString('pt-BR'),
      exames: examesSelecionados.value,
      medico: auth.user?.nome,
      crm: auth.user?.crm,
      especialidade: auth.user?.especialidades?.join(', '),
      cidPrincipal: cidPrincipal.value,
      caraterAtendimento: caraterAtendimento.value
    }
    const html = await gerarHtmlGuiaTiss(params)
    imprimirGuiaTiss(html)
    return
  }

  const pdfMake = await usePdfMake()
  const doc = await buildSolicitacaoExames({
    paciente: agendamento.value?.paciente.nome ?? 'Paciente',
    data: new Date().toLocaleDateString('pt-BR'),
    exames: examesSelecionados.value
      .map(e => ({
        nome: e.nome,
        orientacao: e.orientacao ?? null
      })),
    medico: auth.user?.nome,
    crm: auth.user?.crm,
    especialidade: auth.user?.especialidades?.join(', ')
  })
  pdfMake.createPdf(doc).open()
}

async function gerarComparecimento() {
  const ag = agendamento.value
  if (!ag) return
  const pdfMake = await usePdfMake()
  const dataFormatada = new Date(ag.data + 'T12:00:00').toLocaleDateString('pt-BR')
  const doc = await buildAtestadoComparecimento({
    paciente: ag.paciente.nome,
    data: dataFormatada,
    horario: ag.horario.slice(0, 5),
    medico: auth.user?.nome,
    crm: auth.user?.crm,
    especialidade: auth.user?.especialidades?.join(', ')
  })
  pdfMake.createPdf(doc).open()
}

const cancelandoConsulta = ref(false)
const modalCancelarAberto = ref(false)

async function cancelarAtendimento() {
  if (!agendamento.value || cancelandoConsulta.value) return

  cancelandoConsulta.value = true
  const agendamentoAtual = agendamento.value

  try {
    await agendamentosStore.atualizarStatus(agendamentoAtual.id, 'cancelado', undefined, agendamentoAtual.clinicaId)
    limparDraft()
    cronometro.stop()
    modalCancelarAberto.value = false
    await navigateTo('/dashboard', { replace: true })
  } catch (error) {
    console.error('Erro ao cancelar atendimento', error)
    toast.add({
      title: 'Erro ao cancelar atendimento',
      description: 'Não foi possível devolver o paciente à fila. Tente novamente.',
      color: 'error',
      icon: 'i-lucide-alert-circle'
    })
  } finally {
    cancelandoConsulta.value = false
  }
}

async function finalizarConsulta() {
  if (!agendamento.value || finalizandoConsulta.value) return

  finalizandoConsulta.value = true
  const agendamentoAtual = agendamento.value
  const duracao = cronometro.elapsed

  try {
    await agendamentosStore.atualizarStatus(agendamentoAtual.id, 'atendido', {
      anamnese: anamneseTexto.value,
      diagnosticos: cidSelecionadoLista.value.map((cid, i) => ({
        cid: cid.cid,
        descricao: cid.nome,
        principal: i === 0
      })),
      medicamentos: receitaTexto.value,
      exames: examesSelecionados.value.map(e => ({
        nome: e.nome,
        exame_id: e.exameId ?? null,
        codigo_amb: e.codigo_amb ?? null,
        codigo_alfanumerico: e.codigo_alfanumerico ?? null,
        orientacao: e.orientacao ?? null
      })),
      duracao
    }, agendamentoAtual.clinicaId)
    limparDraft()
    cronometro.stop()
    await navigateTo('/dashboard', { replace: true })
  } catch (error) {
    console.error('Erro ao finalizar consulta', error)
    toast.add({
      title: 'Erro ao finalizar consulta',
      description: 'Não foi possível salvar os dados do atendimento. Tente novamente.',
      color: 'error',
      icon: 'i-lucide-alert-circle'
    })
  } finally {
    finalizandoConsulta.value = false
  }
}
</script>

<template>
  <div class="h-screen flex flex-col">
    <UHeader title="Consulta Atual">
      <template #right>
        <div class="flex items-center gap-2">
          <UBadge
            v-if="draftSalvoEm"
            :color="draftRestaurado ? 'success' : 'neutral'"
            variant="soft"
            icon="i-lucide-save"
          >
            Rascunho salvo às {{ draftSalvoHorario }}
          </UBadge>
          <UBadge
            color="neutral"
            variant="subtle"
          >
            <p>Tempo: {{ cronometro.formatted }}</p>
            <UButton
              :key="cronometro.isRunning ? 'pause' : 'play'"
              :icon="cronometro.isRunning ? 'i-lucide-pause' : 'i-lucide-play'"
              color="neutral"
              variant="ghost"
              size="sm"
              @click="cronometro.isRunning ? cronometro.pause() : cronometro.resume()"
            />
          </UBadge>
        </div>
        <UColorModeButton />
      </template>
    </UHeader>

    <UTabs
      v-model="tabAtiva"
      :items="tabItems"
      color="primary"
      size="lg"
      :ui="{
        content: 'grow min-h-0 flex flex-col',
        list: 'bg-default/75 backdrop-blur border-b border-default rounded-tl-none rounded-tr-none'
      }"
      class="flex-1 overflow-hidden "
    >
      <template #content="{ index }">
        <div
          v-if="index === 0"
          class="px-2 flex flex-col gap-4 py-2 pb-20  grow"
        >
          <UCard
            :ui="{ header: 'p-1 sm:px-2', body: 'p-0 sm:p-0 grow flex flex-col' }"
            class="grow flex flex-col"
          >
            <template #title>
              <div class="flex items-center gap-2">
                <UIcon
                  name="i-lucide-notebook-text"
                  class="text-primary"
                />
                <p class="font-semibold">
                  Anamnese e Evolução
                </p>
              </div>
            </template>
            <div class="shrink-0 flex gap-2 p-2 border-b border-muted">
              <UInputMenu
                v-model="padraoAnamneseSelected"
                :items="padroesAnamneseStore.padroes.map(p => ({ label: p.nome, value: p }))"
                searchable
                placeholder="Inserir Padrão de Anamnese..."
                class="flex-1"
              />
              <UButton
                icon="i-lucide-copy-plus"
                label="Adicionar"
                color="secondary"
                :disabled="!padraoAnamneseSelected"
                @click="adicionarPadraoAnamnese"
              />
            </div>
            <EditorRichText
              v-model="anamneseTexto"
              placeholder="Descreva a anamnese e evolução do paciente..."
              class="grow flex flex-col"
            />
          </UCard>

          <UCard
            :ui="{ header: 'p-1 sm:px-2', body: 'p-2 sm:p-2' }"
          >
            <template #title>
              <div class="flex items-center gap-2">
                <UIcon
                  name="i-lucide-stethoscope"
                  class="text-primary"
                />
                <p class="font-semibold">
                  Diagnósticos (CID-10)
                </p>
              </div>
            </template>

            <div class="flex gap-2">
              <UInputMenu
                v-model="cidTempSelecionado"
                v-model:search-term="searchCid"
                :items="resultadosCid"
                :loading="isLoadingCid"
                label-key="nome"
                placeholder="Buscar CID por código ou nome..."
                icon="i-lucide-search"
                clear
                ignore-filter
                class="flex-1"
              >
                <template #item-label="{ item }">
                  <span class="font-mono text-xs font-semibold text-primary min-w-10">{{ item.cid }}</span>
                  <span class="text-muted"> — </span>
                  <span class="truncate">{{ item.nome }}</span>
                </template>
                <template #empty>
                  <p
                    v-if="erroBuscaCid"
                    class="px-3 py-4 text-sm text-error text-center"
                  >
                    {{ erroBuscaCid }}
                  </p>
                  <p
                    v-else-if="searchCid"
                    class="px-3 py-4 text-sm text-muted text-center"
                  >
                    Nenhum CID encontrado
                  </p>
                </template>
              </UInputMenu>
              <UButton
                icon="i-lucide-plus"
                color="primary"
                :disabled="!cidTempSelecionado"
                @click="adicionarCid(cidTempSelecionado!); cidTempSelecionado = null"
              />
            </div>

            <div
              v-if="cidSelecionadoLista.length"
              class="mt-3 space-y-2"
            >
              <div
                v-for="(cid, i) in cidSelecionadoLista"
                :key="i"
                class="flex items-center justify-between p-2 rounded-lg border border-muted"
              >
                <span class="text-sm">
                  {{ cid.cid }} — {{ cid.nome }}
                  <UBadge
                    v-if="i === 0"
                    size="xs"
                    color="primary"
                    variant="soft"
                  >Principal</UBadge>
                </span>
                <UButton
                  icon="i-lucide-x"
                  size="xs"
                  color="error"
                  variant="ghost"
                  @click="removerCid(i)"
                />
              </div>
            </div>
            <p
              v-else
              class="text-sm text-muted italic mt-3 text-center"
            >
              Nenhum CID selecionado
            </p>
          </UCard>
        </div>

        <div
          v-if="index === 2"
          class="px-2 flex flex-col gap-4 py-2  grow"
        >
          <UCard
            :ui="{ body: 'grow flex flex-col p-0 sm:p-0' }"
            class="grow flex flex-col"
          >
            <template #title>
              <div class="flex items-center gap-2">
                <UIcon
                  name="i-lucide-pill"
                  class="text-primary"
                />
                <p class="font-semibold">
                  Receita Digital
                </p>
              </div>
            </template>

            <div class="flex flex-col gap-4 grow p-4">
              <div class="shrink-0 flex gap-2">
                <UInputMenu
                  v-model="padraoReceitaSelected"
                  :items="padroesStore.receitas.map(p => ({ label: p.nome, value: p }))"
                  searchable
                  placeholder="Selecionar padrão de receita..."
                  class="flex-1"
                />
                <UButton
                  icon="i-lucide-copy-plus"
                  label="Adicionar Padrão"
                  color="secondary"
                  :disabled="!padraoReceitaSelected"
                  @click="adicionarPadraoReceita"
                />
              </div>

              <div class="shrink-0 flex items-end gap-3 p-4 rounded-lg border border-muted bg-neutral-50 dark:bg-neutral-900">
                <UFormField
                  label="Nome do medicamento"
                  class="flex-1"
                >
                  <UInput
                    v-model="remedioNome"
                    placeholder="Ex: Amoxicilina"
                    class="w-full"
                  />
                </UFormField>
                <UFormField
                  label="Dosagem"
                  class="w-48"
                >
                  <UInput
                    v-model="remedioDosagem"
                    placeholder="Ex: 500mg 3x/dia"
                  />
                </UFormField>
                <UFormField
                  label="Detalhes"
                  class="flex-1"
                >
                  <UInput
                    v-model="remedioDetalhes"
                    placeholder="Observações..."
                    class="w-full"
                  />
                </UFormField>
                <UButton
                  icon="i-lucide-plus"
                  label="Adicionar"
                  color="primary"
                  :disabled="!remedioNome && !remedioDosagem"
                  @click="adicionarRemedio"
                />
              </div>

              <p
                v-if="!padroesStore.receitas.length"
                class="shrink-0 text-sm text-muted italic"
              >
                Nenhum padrão de receita cadastrado. Crie padrões em "Padrões de Solicitações".
              </p>

              <UTextarea
                v-model="receitaTexto"
                placeholder="Os medicamentos adicionados aparecerão aqui..."
                class="w-full grow min-h-0"
                :ui="{ base: 'h-full min-h-0' }"
              />

              <div class="grid grid-cols-2 gap-3 w-full">
                <UButton
                  icon="i-lucide-file-text"
                  label="Gerar Receita (PDF)"
                  color="primary"
                  class="w-full shrink-0"
                  :disabled="!receitaTexto.trim()"
                  @click="gerarReceitaPdf"
                />
                <UButton
                  icon="lucide:file-warning"
                  label="Gerar Receita Especial"
                  color="warning"
                  class="w-full shrink-0"
                  :disabled="!receitaTexto.trim()"
                  @click="gerarReceitaEspecialPdf"
                />
              </div>
            </div>
          </UCard>
        </div>

        <div
          v-if="index === 1"
          class="px-2 flex flex-col gap-4 py-2  grow"
        >
          <UCard
            :ui="{ body: 'grow flex flex-col p-0 sm:p-0' }"
            class="grow flex flex-col"
          >
            <template #title>
              <div class="flex items-center justify-between">
                <div class="flex items-center gap-2">
                  <UIcon
                    name="i-lucide-flask-conical"
                    class="text-primary"
                  />
                  <p class="font-semibold">
                    Pedido de Exames
                  </p>
                </div>
                <div class="flex items-center gap-2">
                  <span class="text-sm text-muted">
                    {{ caraterAtendimento ? 'U - Urgência/Emergência' : 'E - Eletiva' }}
                  </span>
                  <USwitch v-model="caraterAtendimento" />
                </div>
              </div>
            </template>

            <div class="flex flex-col gap-4 grow p-4">
              <div class="shrink-0 flex gap-2">
                <UInputMenu
                  v-model="exameTemplateSelected"
                  :items="padroesStore.exames.map(p => ({ label: p.nome, value: p }))"
                  searchable
                  placeholder="Selecionar padrão de exames..."
                  class="flex-1 w-full"
                />
                <UButton
                  icon="i-lucide-copy-plus"
                  label="Adicionar Padrão"
                  color="secondary"
                  :disabled="!exameTemplateSelected"
                  @click="adicionarPadraoExame"
                />
              </div>

              <UFormField
                label="Nome do exame"
                class="w-full"
              >
                <div class="flex gap-2">
                  <UInputMenu
                    v-model="exameSelecionado"
                    v-model:search-term="buscaTermoExame"
                    :items="sugestoesExames"
                    :loading="carregandoExames"
                    label-key="nome"
                    placeholder="Buscar exame..."
                    class="flex-1 w-full"
                    clear
                    ignore-filter
                  >
                    <template #item-label="{ item }">
                      <span class="text-sm">
                        {{ item.codigo_alfanumerico ? `${item.codigo_alfanumerico} — ` : '' }}{{ item.nome }}{{ item.codigo_amb ? ` (${item.codigo_amb})` : '' }}
                      </span>
                    </template>
                    <template #empty>
                      <p
                        v-if="erroBuscaExames"
                        class="px-3 py-4 text-sm text-error text-center"
                      >
                        {{ erroBuscaExames }}
                      </p>
                      <p
                        v-else-if="buscaTermoExame.trim().length >= 2"
                        class="px-3 py-4 text-sm text-muted text-center"
                      >
                        Nenhum exame encontrado
                      </p>
                    </template>
                  </UInputMenu>
                  <UButton
                    icon="i-lucide-plus"
                    label="Adicionar"
                    color="primary"
                    variant="soft"
                    :disabled="!buscaTermoExame.trim()"
                    @click="adicionarExameManual"
                  />
                </div>
              </UFormField>
              <!-- revisar dps esse h-30 -->
              <UCard
                class="grow flex flex-col min-h-0"
                :ui="{
                  body: 'overflow-y-auto h-30 p-3 grow',
                  header: 'shrink-0'
                }"
              >
                <template #title>
                  <div class="flex items-center justify-between">
                    <span class="text-sm font-medium">Exames selecionados</span>
                    <span class="text-xs text-muted">{{ examesSelecionados.length }} exame(s)</span>
                  </div>
                </template>

                <div
                  v-if="examesSelecionados.length"
                  class="space-y-2"
                >
                  <div
                    v-for="(exameItem, i) in examesSelecionados"
                    :key="i"
                    class="flex items-center justify-between p-3 rounded-lg border border-muted"
                  >
                    <span class="text-sm">{{ exameItem.nome }}</span>
                    <div class="flex gap-3 items-center">
                      <UButton
                        variant="link"
                        :icon="exameTemOrientacao(exameItem) ? 'i-lucide-message-square-warning' : 'i-lucide-plus'"
                        @click="adicionarOrientacao(exameItem)"
                      >
                        {{ exameTemOrientacao(exameItem) ? 'Editar Orientação' : 'Adicionar Orientação' }}
                      </UButton>
                      <UButton
                        icon="i-lucide-x"
                        color="error"
                        variant="ghost"
                        size="sm"
                        @click="removerExameDaLista(i)"
                      />
                    </div>
                  </div>
                </div>
                <p
                  v-else
                  class="text-sm text-muted italic py-4 text-center"
                >
                  Nenhum exame adicionado.
                </p>
              </UCard>

              <UButton
                icon="i-lucide-file-text"
                label="Gerar Solicitação (PDF)"
                color="primary"
                class="w-full shrink-0"
                :disabled="!examesSelecionados.length"
                @click="gerarSolicitacaoExames"
              />
            </div>
          </UCard>
        </div>

        <div
          v-if="index === 3"
          class="px-2 flex flex-col gap-4 py-2  grow"
        >
          <UCard>
            <template #title>
              <div class="flex items-center justify-center gap-2">
                <UIcon
                  name="i-lucide-printer"
                  class="text-primary"
                />
                <p class="font-semibold">
                  Documentos
                </p>
              </div>
            </template>
            <div class="grid grid-cols-2 gap-4">
              <UButton
                icon="i-lucide-file-check"
                label="Atestado de Comparecimento"
                color="primary"
                class="w-full p-3 text-lg font-bold"
                @click="void gerarComparecimento()"
              />
              <UButton
                icon="i-lucide-stamp"
                label="Atestado Médico"
                color="neutral"
                class="w-full p-3 text-lg font-bold"
                @click="void (showAtestadoModal = true)"
              />
              <UButton
                icon="i-lucide-send"
                label="Encaminhamento Médico"
                color="secondary"
                class="w-full p-3 text-lg font-bold"
                @click="void (showEncaminhamentoModal = true)"
              />
              <UButton
                icon="i-lucide-clipboard-list"
                label="Solicitação de Procedimento"
                color="tertiary"
                class="w-full p-3 text-lg font-bold"
                @click="void (showProcedimentoModal = true)"
              />
              <UButton
                icon="i-lucide-flask-conical"
                label="Gerar Exames (PDF)"
                color="warning"
                class="w-full p-3 text-lg font-bold"
                :disabled="!examesSelecionados.length"
                @click="void (tabAtiva = '1')"
              />
              <UButton
                icon="i-lucide-file-text"
                label="Gerar Receita (PDF)"
                color="quaternary"
                class="w-full p-3 text-lg font-bold"
                :disabled="!receitaTexto.trim()"
                @click="void (tabAtiva = '2')"
              />
            </div>
          </UCard>
          <UCard
            :ui="{ body: 'flex justify-center gap-4' }"
          >
            <UButton
              icon="i-lucide-x-circle"
              label="Cancelar atendimento"
              color="error"
              size="xl"
              class="p-3 text-lg font-bold min-w-110"
              :loading="cancelandoConsulta"
              :disabled="cancelandoConsulta"
              @click="void (modalCancelarAberto = true)"
            />
            <UButton
              icon="i-lucide-check-circle"
              label="Finalizar Consulta"
              color="success"
              size="xl"
              class="p-3 text-lg font-bold min-w-110"
              :loading="finalizandoConsulta"
              :disabled="finalizandoConsulta"
              @click="void finalizarConsulta()"
            />
          </UCard>
        </div>
      </template>
    </UTabs>

    <AtestadoGerarModal
      v-model:open="showAtestadoModal"
      :agendamento="agendamento"
      :data-atendimento="agendamento?.data"
      :documento="documentoAtestado"
      @saved="atualizarDocumentoMedico"
    />
    <EncaminhamentoGerarModal
      v-model:open="showEncaminhamentoModal"
      :agendamento="agendamento"
      :data-atendimento="agendamento?.data"
      :documento="documentoEncaminhamento"
      @saved="atualizarDocumentoMedico"
    />
    <ProcedimentoGerarModal
      v-model:open="showProcedimentoModal"
      :agendamento="agendamento"
      :data-atendimento="agendamento?.data"
      :documento="documentoProcedimento"
      @saved="atualizarDocumentoMedico"
    />
    <ProcedimentoGerarModal
      v-model:open="showOpmeModal"
      :agendamento="agendamento"
      :data-atendimento="agendamento?.data"
      :documento="documentoOpme"
      aba-inicial="opme"
      @saved="atualizarDocumentoMedico"
    />
    <OrientacaoExameModal
      v-model:open="showOrientacaoExamesModal"
      :exame="exame"
      :agendamento="agendamento"
      :data-atendimento="agendamento?.data"
      @saved="salvarOrientacaoExame"
    />
    <ModalConfirmacao
      :abrir="modalCancelarAberto"
      titulo="Cancelar atendimento?"
      descricao="O paciente será devolvido à fila de espera e o atendimento atual será descartado. Tem certeza?"
      texto-confirma="Cancelar Atendimento"
      cor-confirma="error"
      @fechar="modalCancelarAberto = false"
      @confirmar="void cancelarAtendimento()"
    />
  </div>
</template>
