<script setup lang="ts">
import type { AgendamentoComPaciente, DocumentoMedico, Paciente, ProcedimentoCatalogo, ProcedimentoSelecionado, SolicitacaoOpmeDocumentoDados, SolicitacaoProcedimentoDocumentoDados } from '~/types'
import { usePdfMake } from '~/utils/pdf'
import { buildSolicitacaoOpme, buildSolicitacaoProcedimento } from '~/utils/pdf-documents'
import { gerarHtmlGuiaInternacao, gerarHtmlGuiaOpme, imprimirGuiaInternacao, imprimirGuiaOpme } from '~/utils/guia-tiss'

const props = defineProps<{
  paciente?: Paciente
  agendamento?: AgendamentoComPaciente | null
  dataAtendimento?: string
  documento?: DocumentoMedico | null
  abaInicial?: 'internacao' | 'opme'
}>()

const emit = defineEmits<{
  saved: [documento: DocumentoMedico]
}>()

const open = defineModel<boolean>('open', { default: false })

const tabAtiva = ref('0')

const tabItems = [
  { label: 'Procedimento', icon: 'i-lucide-notebook-text' },
  { label: 'OPME', icon: 'i-lucide-flask-conical' }
]

const agendamentosStore = useAgendamentosStore()
const toast = useToast()

const paciente = computed(() => props.paciente ?? props.agendamento?.paciente ?? agendamentosStore.emAtendimento?.paciente ?? null)
const medSpdataAtendimentoId = computed(() => props.agendamento?.id ?? agendamentosStore.emAtendimento?.id ?? null)
const podeEditar = computed(() => props.documento?.podeEditar ?? true)

function hojeIso() {
  const d = new Date()
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}

const dataAtendimentoPadrao = computed(() => props.dataAtendimento ?? props.agendamento?.data ?? hojeIso())

const data = ref(dataAtendimentoPadrao.value)
const procedimentoSelecionado = ref<ProcedimentoCatalogo | null>(null)
const buscaTermoProcedimento = ref('')
const sugestoesProcedimentos = ref<ProcedimentoCatalogo[]>([])
const procedimentosSelecionados = ref<ProcedimentoSelecionado[]>([])
const carregandoProcedimentos = ref(false)
const salvando = ref(false)

const convenioNaoParticular = computed(() => {
  const convenio = (paciente.value?.convenio ?? '').toLowerCase().trim()
  return Boolean(convenio && convenio !== 'particular')
})

const tiposInternacao = [
  '1 - clínica',
  '2 - cirurgia',
  '3 - obstétrica',
  '4 - pediátrica',
  '5 - psiquiátrica'
]

const regimesInternacao = [
  '1 - hospitalar',
  '2 - hospital-dia',
  '3 - domiciliar'
]

const caraterInternacao = ref(false)
const atendimentoRN = ref(false)
const tipoInternacao = ref<string | undefined>(undefined)
const regimeInternacao = ref<string | undefined>(undefined)
const quantidadeDiarias = ref<number | null>(null)
const indicacaoClinica = ref('')

type OpmeItem = { codigo: string, nome: string, quantidade: number }

const opmeItens = ref<OpmeItem[]>([])
const opmeCodigo = ref('')
const opmeNome = ref('')
const opmeQuantidade = ref<number | null>(1)

let buscaProcedimentoTimeout: ReturnType<typeof setTimeout> | null = null
let procedimentosController: AbortController | null = null
let procedimentosRequestId = 0

function normalizarId(valor: unknown) {
  if (valor === null || valor === undefined || valor === '') return null

  const numero = Number(valor)
  return Number.isInteger(numero) && numero > 0 ? numero : null
}

function normalizarNumero(valor: unknown) {
  if (valor === null || valor === undefined || valor === '') return null

  const numero = Number(valor)
  return Number.isFinite(numero) ? numero : null
}

function normalizarTexto(valor: unknown) {
  return typeof valor === 'string' ? valor.trim() : ''
}

function normalizarProcedimentoSelecionado(valor: unknown): ProcedimentoSelecionado | null {
  if (typeof valor === 'string') {
    const nome = valor.trim()
    return nome ? { procedimento_id: null, nome } : null
  }

  if (!valor || typeof valor !== 'object') return null

  const item = valor as Record<string, unknown>
  const nome = normalizarTexto(item.nome ?? item.descricao ?? item.label)
  const procedimentoId = normalizarId(item.procedimento_id ?? item.procedimentoId ?? item.id)

  if (!nome) return null

  return {
    procedimento_id: procedimentoId,
    nome,
    codigo_procedimento: normalizarNumero(item.codigo_procedimento ?? item.codigoProcedimento),
    tipo_ato_codigo: normalizarId(item.tipo_ato_codigo ?? item.tipoAtoCodigo),
    tipo_ato_nome: normalizarTexto(item.tipo_ato_nome ?? item.tipoAtoNome) || null,
    exige_autorizacao: normalizarNumero(item.exige_autorizacao ?? item.exigeAutorizacao),
    qtde_max_guia: normalizarNumero(item.qtde_max_guia ?? item.qtdeMaxGuia)
  }
}

function procedimentoExisteNaLista(lista: ProcedimentoSelecionado[], procedimento: ProcedimentoSelecionado) {
  const nome = procedimento.nome.trim().toLocaleLowerCase('pt-BR')

  return lista.some((atual) => {
    if (atual.procedimento_id && procedimento.procedimento_id && atual.procedimento_id === procedimento.procedimento_id) return true
    return atual.nome.trim().toLocaleLowerCase('pt-BR') === nome
  })
}

function normalizarListaProcedimentos(valor: unknown) {
  const procedimentos: ProcedimentoSelecionado[] = []
  const itens = typeof valor === 'string'
    ? valor.split(/\r?\n/).map(linha => linha.replace(/^[-•\s]+/, '').trim()).filter(Boolean)
    : Array.isArray(valor)
      ? valor
      : valor
        ? [valor]
        : []

  for (const item of itens) {
    const procedimento = normalizarProcedimentoSelecionado(item)
    if (!procedimento || procedimentoExisteNaLista(procedimentos, procedimento)) continue
    procedimentos.push(procedimento)
  }

  return procedimentos
}

function procedimentoLabel(procedimento: ProcedimentoSelecionado | ProcedimentoCatalogo) {
  const codigo = procedimento.codigo_procedimento ? `${procedimento.codigo_procedimento} - ` : ''
  return `${codigo}${procedimento.nome}`
}

const descricaoProcedimentos = computed(() => (
  procedimentosSelecionados.value
    .map(procedimentoLabel)
    .join('\n')
))

function limparBuscaProcedimentos() {
  procedimentosRequestId++
  procedimentosController?.abort()
  sugestoesProcedimentos.value = []
}

watch(buscaTermoProcedimento, (val) => {
  if (buscaProcedimentoTimeout) clearTimeout(buscaProcedimentoTimeout)

  const termo = val.trim()
  if (termo.length < 2) {
    limparBuscaProcedimentos()
    return
  }

  buscaProcedimentoTimeout = setTimeout(() => {
    buscarProcedimentos(termo)
  }, 300)
})

async function buscarProcedimentos(q: string) {
  const termo = q.trim()
  if (termo.length < 2) return

  const requestId = ++procedimentosRequestId
  procedimentosController?.abort()
  procedimentosController = new AbortController()

  carregandoProcedimentos.value = true
  try {
    const data = await $fetch<{ procedimentos: ProcedimentoCatalogo[] }>('/api/procedimentos/buscar', {
      query: { q: termo },
      signal: procedimentosController.signal
    })

    if (requestId !== procedimentosRequestId) return
    if (buscaTermoProcedimento.value.trim() !== termo) return

    sugestoesProcedimentos.value = data.procedimentos || []
  } catch (error) {
    if (error instanceof Error && error.name === 'AbortError') return
    if (requestId !== procedimentosRequestId) return
    sugestoesProcedimentos.value = []
  } finally {
    carregandoProcedimentos.value = false
  }
}

function adicionarProcedimento(valor: unknown) {
  const procedimento = normalizarProcedimentoSelecionado(valor)
  if (!procedimento) return
  if (procedimentoExisteNaLista(procedimentosSelecionados.value, procedimento)) return

  procedimentosSelecionados.value.push(procedimento)
  procedimentoSelecionado.value = null
  buscaTermoProcedimento.value = ''
  sugestoesProcedimentos.value = []
}

function removerProcedimentoDaLista(index: number) {
  procedimentosSelecionados.value.splice(index, 1)
}

function normalizarListaOpme(valor: unknown): OpmeItem[] {
  const itens = typeof valor === 'string'
    ? valor.split(/\r?\n/).map(linha => linha.replace(/^[-•\s]+/, '').trim()).filter(Boolean).map(nome => ({ nome }))
    : Array.isArray(valor)
      ? valor
      : valor
        ? [valor]
        : []

  const opmes: OpmeItem[] = []
  const nomes = new Set<string>()

  for (const item of itens) {
    const nome = normalizarTexto(typeof item === 'object' && item ? (item as Record<string, unknown>).nome ?? (item as Record<string, unknown>).descricao : '')
    if (!nome) continue

    const chave = nome.toLocaleLowerCase('pt-BR')
    if (nomes.has(chave)) continue
    nomes.add(chave)

    const codigo = normalizarTexto(typeof item === 'object' && item ? (item as Record<string, unknown>).codigo : '')
    const quantidade = normalizarNumero(typeof item === 'object' && item ? (item as Record<string, unknown>).quantidade ?? 1 : 1)
    opmes.push({ codigo, nome, quantidade: quantidade && quantidade > 0 ? quantidade : 1 })
  }

  return opmes
}

function adicionarOpme() {
  const nome = opmeNome.value.trim()
  if (!nome) return

  const jaExiste = opmeItens.value.some(i => i.nome.toLocaleLowerCase('pt-BR') === nome.toLocaleLowerCase('pt-BR'))
  if (jaExiste) return

  opmeItens.value.push({
    codigo: opmeCodigo.value.trim(),
    nome,
    quantidade: opmeQuantidade.value && opmeQuantidade.value > 0 ? opmeQuantidade.value : 1
  })
  opmeCodigo.value = ''
  opmeNome.value = ''
  opmeQuantidade.value = 1
}

function removerOpme(index: number) {
  opmeItens.value.splice(index, 1)
}

const CID_CODE_PATTERN = /^[A-Za-z][0-9.]*$/
const MAX_CIDS = 4

type CidResultado = { cid: string, nome: string }

let buscaCidTimeout: ReturnType<typeof setTimeout> | null = null
let cidController: AbortController | null = null
let cidRequestId = 0

const searchCid = ref('')
const resultadosCid = ref<CidResultado[]>([])
const cidTempSelecionado = ref<CidResultado | null>(null)
const cidSelecionadoLista = ref<CidResultado[]>([])
const isLoadingCid = ref(false)
const erroBuscaCid = ref('')

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

watch(searchCid, (val) => {
  if (buscaCidTimeout) clearTimeout(buscaCidTimeout)

  if (!podeBuscarCid(val)) {
    limparResultadosCid()
    return
  }

  buscaCidTimeout = setTimeout(() => {
    buscarCid(val)
  }, 300)
})

function adicionarCid(item: CidResultado) {
  if (cidSelecionadoLista.value.length >= MAX_CIDS) return
  const jaExiste = cidSelecionadoLista.value.some(c => c.cid === item.cid)
  if (jaExiste) return
  cidSelecionadoLista.value.push(item)
  searchCid.value = ''
  resultadosCid.value = []
}

function removerCid(index: number) {
  cidSelecionadoLista.value.splice(index, 1)
}

function preencherFormulario() {
  procedimentosSelecionados.value = []
  procedimentoSelecionado.value = null
  buscaTermoProcedimento.value = ''
  sugestoesProcedimentos.value = []
  caraterInternacao.value = false
  atendimentoRN.value = false
  tipoInternacao.value = undefined
  regimeInternacao.value = undefined
  quantidadeDiarias.value = null
  indicacaoClinica.value = ''
  opmeItens.value = []
  opmeCodigo.value = ''
  opmeNome.value = ''
  opmeQuantidade.value = 1
  cidSelecionadoLista.value = []
  cidTempSelecionado.value = null
  searchCid.value = ''
  resultadosCid.value = []
  erroBuscaCid.value = ''

  if (props.documento?.tipoDocumento === 'SOLICITACAO_OPME') {
    const dados = props.documento.dados as SolicitacaoOpmeDocumentoDados
    data.value = dados?.data ?? dataAtendimentoPadrao.value
    opmeItens.value = normalizarListaOpme(dados?.opmeItens ?? dados?.opmeSolicitados)
    indicacaoClinica.value = dados?.indicacaoClinica ?? ''
    tabAtiva.value = '1'
    return
  }

  const dados = props.documento?.tipoDocumento === 'SOLICITACAO_PROCEDIMENTO'
    ? props.documento.dados as SolicitacaoProcedimentoDocumentoDados
    : null

  data.value = dados?.data ?? dataAtendimentoPadrao.value
  const procedimentos = normalizarListaProcedimentos(dados?.procedimentos)
  procedimentosSelecionados.value = procedimentos.length
    ? procedimentos
    : normalizarListaProcedimentos(dados?.descricao)
  caraterInternacao.value = dados?.caraterInternacao ?? false
  atendimentoRN.value = dados?.atendimentoRN ?? false
  tipoInternacao.value = dados?.tipoInternacao ?? undefined
  regimeInternacao.value = dados?.regimeInternacao ?? undefined
  quantidadeDiarias.value = dados?.quantidadeDiarias ?? null
  indicacaoClinica.value = dados?.indicacaoClinica ?? ''
  cidSelecionadoLista.value = (dados?.cids ?? []).slice(0, MAX_CIDS).map(c => ({ cid: c.cid, nome: c.nome ?? '' }))

  tabAtiva.value = props.abaInicial === 'opme' ? '1' : '0'
}

watch(
  () => [open.value, props.documento?.id, props.documento?.updatedAt, dataAtendimentoPadrao.value] as const,
  ([isOpen]) => {
    if (isOpen) preencherFormulario()
  },
  { immediate: true }
)

function formatarDataPdf(dataISO: string) {
  if (!dataISO) return ''
  return new Date(dataISO + 'T12:00:00').toLocaleDateString('pt-BR')
}

const podeEnviar = computed(() => {
  if (!podeEditar.value) return Boolean(props.documento)
  if (!medSpdataAtendimentoId.value || !data.value) return false

  if (tabAtiva.value === '1') return opmeItens.value.length > 0
  return procedimentosSelecionados.value.length > 0
})

const botaoLabel = computed(() => podeEditar.value ? 'Salvar e Imprimir' : 'Imprimir')

async function gerarPdf(documento: DocumentoMedico) {
  const pdfMake = await usePdfMake()
  const pacienteNome = paciente.value?.nome ?? 'Paciente'

  if (documento.tipoDocumento === 'SOLICITACAO_OPME') {
    const dados = documento.dados as SolicitacaoOpmeDocumentoDados
    const dataFormatada = formatarDataPdf(dados.data)
    const opmeItensLista = normalizarListaOpme(dados.opmeItens ?? dados.opmeSolicitados)

    if (convenioNaoParticular.value) {
      const html = await gerarHtmlGuiaOpme({
        paciente: pacienteNome,
        data: dataFormatada,
        convenio: paciente.value?.convenio,
        idConvenioSpdata: paciente.value?.idConvenioSpdata,
        medico: dados.medico ?? undefined,
        crm: dados.crm ?? undefined,
        especialidade: dados.especialidade ?? undefined,
        indicacaoClinica: dados.indicacaoClinica ?? '',
        opmeItens: opmeItensLista
      })
      imprimirGuiaOpme(html)
      return
    }

    const doc = await buildSolicitacaoOpme({
      paciente: pacienteNome,
      data: dataFormatada,
      opmeItens: opmeItensLista,
      indicacaoClinica: dados.indicacaoClinica ?? undefined,
      medico: dados.medico ?? undefined,
      crm: dados.crm ?? undefined,
      especialidade: dados.especialidade ?? undefined
    })
    pdfMake.createPdf(doc).open()
    return
  }

  if (documento.tipoDocumento !== 'SOLICITACAO_PROCEDIMENTO') return

  const dados = documento.dados as SolicitacaoProcedimentoDocumentoDados
  const procedimentos = normalizarListaProcedimentos(dados.procedimentos)
  const dataFormatada = formatarDataPdf(dados.data)

  if (convenioNaoParticular.value) {
    const html = await gerarHtmlGuiaInternacao({
      paciente: pacienteNome,
      data: dataFormatada,
      convenio: paciente.value?.convenio,
      idConvenioSpdata: paciente.value?.idConvenioSpdata,
      medico: dados.medico ?? undefined,
      crm: dados.crm ?? undefined,
      especialidade: dados.especialidade ?? undefined,
      caraterInternacao: dados.caraterInternacao,
      tipoInternacao: dados.tipoInternacao,
      regimeInternacao: dados.regimeInternacao,
      quantidadeDiarias: dados.quantidadeDiarias ?? null,
      indicacaoClinica: dados.indicacaoClinica ?? '',
      atendimentoRN: dados.atendimentoRN,
      cids: dados.cids,
      procedimentos: procedimentos.length ? procedimentos : normalizarListaProcedimentos(dados.descricao)
    })
    imprimirGuiaInternacao(html)
    return
  }

  const doc = await buildSolicitacaoProcedimento({
    paciente: pacienteNome,
    data: dataFormatada,
    descricao: dados.descricao,
    procedimentos: procedimentos.length ? procedimentos : normalizarListaProcedimentos(dados.descricao),
    medico: dados.medico ?? undefined,
    crm: dados.crm ?? undefined,
    especialidade: dados.especialidade ?? undefined
  })
  pdfMake.createPdf(doc).open()
}

async function fecharEAbrirPdf(documento: DocumentoMedico) {
  open.value = false
  await nextTick()
  await gerarPdf(documento)
}

async function salvarEImprimir() {
  if (!podeEnviar.value) return

  if (!podeEditar.value && props.documento) {
    await fecharEAbrirPdf(props.documento)
    return
  }

  salvando.value = true
  try {
    const ehOpme = tabAtiva.value === '1'
    const tipo = ehOpme ? 'SOLICITACAO_OPME' : 'SOLICITACAO_PROCEDIMENTO'
    const dados = ehOpme
      ? {
          data: data.value,
          opmeItens: opmeItens.value.map(i => ({ codigo: i.codigo || undefined, nome: i.nome, quantidade: i.quantidade })),
          opmeSolicitados: opmeItens.value.map(i => i.nome).join('\n'),
          indicacaoClinica: indicacaoClinica.value.trim() || undefined
        }
      : {
          data: data.value,
          descricao: descricaoProcedimentos.value,
          procedimentos: procedimentosSelecionados.value,
          caraterInternacao: convenioNaoParticular.value ? caraterInternacao.value : undefined,
          tipoInternacao: convenioNaoParticular.value ? tipoInternacao.value : undefined,
          regimeInternacao: convenioNaoParticular.value ? regimeInternacao.value : undefined,
          quantidadeDiarias: convenioNaoParticular.value ? quantidadeDiarias.value : undefined,
          indicacaoClinica: convenioNaoParticular.value ? (indicacaoClinica.value.trim() || undefined) : undefined,
          atendimentoRN: convenioNaoParticular.value ? atendimentoRN.value : undefined,
          cids: convenioNaoParticular.value ? cidSelecionadoLista.value.map(c => ({ cid: c.cid, nome: c.nome })) : undefined
        }

    const documento = await $fetch<DocumentoMedico>(`/api/documentos-medicos/${medSpdataAtendimentoId.value}/${tipo}`, {
      method: 'PUT',
      body: {
        dados
      }
    })

    emit('saved', documento)
    await fecharEAbrirPdf(documento)
  } catch {
    toast.add({
      title: 'Erro ao salvar solicitação',
      description: 'Não foi possível salvar o documento médico.',
      color: 'error',
      icon: 'i-lucide-alert-circle'
    })
  } finally {
    salvando.value = false
  }
}

onUnmounted(() => {
  if (buscaProcedimentoTimeout) clearTimeout(buscaProcedimentoTimeout)
  procedimentosController?.abort()
  if (buscaCidTimeout) clearTimeout(buscaCidTimeout)
  cidController?.abort()
})
</script>

<template>
  <UModal
    v-model:open="open"
    fullscreen
    :ui="{ content: 'max-h-dvh', body: 'min-h-0 overflow-y-auto p-0', footer: 'shrink-0' }"
  >
    <template #header>
      <div class="flex items-center justify-between">
        <h2 class="text-lg font-semibold">
          Solicitação de Procedimento
        </h2>
        <UButton
          icon="i-lucide-x"
          aria-label="Fechar solicitação de procedimento"
          color="neutral"
          variant="ghost"
          @click="void (open = false)"
        />
      </div>
    </template>

    <template #body>
      <div class="flex justify-center">
        <UTabs
          v-model="tabAtiva"
          :items="tabItems"
          color="primary"
          size="lg"
          :ui="{
            content: 'grow min-h-0 flex flex-col',
            list: 'bg-default/75 backdrop-blur border-b border-default rounded-tl-none rounded-tr-none'
          }"
          class="w-full min-w-0 lg:max-w-[60%]"
        >
          <template #content="{ index }">
            <div
              v-if="index === 0"
              class="space-y-4 p-4 sm:p-6"
            >
              <div class="flex flex-col gap-4 sm:flex-row">
                <UFormField
                  label="Paciente"
                  class="flex-1"
                >
                  <UInput
                    :model-value="paciente?.nome ?? '—'"
                    disabled
                    class="w-full"
                  />
                </UFormField>

                <UFormField
                  label="Data"
                  class="sm:w-44"
                >
                  <UInput
                    v-model="data"
                    type="date"
                    :disabled="!podeEditar"
                    class="w-full"
                  />
                </UFormField>
              </div>

              <UFormField label="Procedimentos">
                <div class="flex flex-col gap-2 sm:flex-row">
                  <UInputMenu
                    v-model="procedimentoSelecionado"
                    v-model:search-term="buscaTermoProcedimento"
                    :items="sugestoesProcedimentos"
                    :loading="carregandoProcedimentos"
                    label-key="nome"
                    placeholder="Buscar procedimento por nome, código ou tipo..."
                    icon="i-lucide-search"
                    clear
                    ignore-filter
                    :disabled="!podeEditar"
                    class="flex-1 w-full"
                  >
                    <template #item-label="{ item }">
                      <div class="min-w-0 flex flex-col">
                        <span class="text-sm truncate">{{ procedimentoLabel(item) }}</span>
                        <span
                          v-if="item.tipo_ato_nome"
                          class="text-xs text-muted truncate"
                        >
                          {{ item.tipo_ato_nome }}
                        </span>
                      </div>
                    </template>
                    <template #empty>
                      <p
                        v-if="buscaTermoProcedimento"
                        class="px-3 py-4 text-sm text-muted text-center"
                      >
                        Nenhum procedimento encontrado
                      </p>
                    </template>
                  </UInputMenu>
                  <UButton
                    icon="i-lucide-plus"
                    label="Adicionar"
                    color="primary"
                    variant="soft"
                    :disabled="!podeEditar || !procedimentoSelecionado"
                    @click="adicionarProcedimento(procedimentoSelecionado)"
                  />
                </div>
              </UFormField>

              <UCard
                :ui="{ body: 'p-3' }"
              >
                <template #title>
                  <div class="flex items-center justify-between">
                    <span class="text-sm font-medium">Procedimentos selecionados</span>
                    <span class="text-xs text-muted">{{ procedimentosSelecionados.length }} procedimento(s)</span>
                  </div>
                </template>

                <div
                  v-if="procedimentosSelecionados.length"
                  class="space-y-2"
                >
                  <div
                    v-for="(procedimento, posicao) in procedimentosSelecionados"
                    :key="procedimento.procedimento_id ?? `${procedimento.nome}-${posicao}`"
                    class="flex flex-col items-stretch justify-between gap-3 rounded-lg border border-muted p-3 sm:flex-row sm:items-start"
                  >
                    <div class="min-w-0 space-y-1">
                      <p class="text-sm font-medium truncate">
                        {{ procedimentoLabel(procedimento) }}
                      </p>
                      <div class="flex flex-wrap gap-2">
                        <UBadge
                          v-if="procedimento.tipo_ato_nome"
                          size="xs"
                          color="neutral"
                          variant="soft"
                        >
                          {{ procedimento.tipo_ato_nome }}
                        </UBadge>
                        <UBadge
                          v-if="procedimento.exige_autorizacao"
                          size="xs"
                          color="warning"
                          variant="soft"
                        >
                          Exige autorização
                        </UBadge>
                        <UBadge
                          v-if="!procedimento.procedimento_id"
                          size="xs"
                          color="neutral"
                          variant="outline"
                        >
                          Legado
                        </UBadge>
                      </div>
                    </div>
                    <UButton
                      v-if="podeEditar"
                      icon="i-lucide-x"
                      :aria-label="`Remover procedimento ${procedimento.nome}`"
                      color="error"
                      variant="ghost"
                      size="sm"
                      class="self-end sm:self-auto"
                      @click="removerProcedimentoDaLista(posicao)"
                    />
                  </div>
                </div>
                <p
                  v-else
                  class="text-sm text-muted italic py-4 text-center"
                >
                  Nenhum procedimento selecionado.
                </p>
              </UCard>

              <UCard
                v-if="convenioNaoParticular"
                :ui="{ body: 'p-4 space-y-4' }"
              >
                <div class="flex flex-col gap-4 sm:flex-row">
                  <UFormField label="Caráter de internação">
                    <div class="flex items-center gap-2">
                      <span class="text-sm">
                        {{ caraterInternacao ? 'U - Urgência/Emergência' : 'E - Eletiva' }}
                      </span>
                      <USwitch
                        v-model="caraterInternacao"
                        :disabled="!podeEditar"
                      />
                    </div>
                  </UFormField>

                  <UFormField label="Atendimento a RN">
                    <div class="flex items-center gap-2">
                      <span class="text-sm">
                        {{ atendimentoRN ? 'S - Sim' : 'N - Não' }}
                      </span>
                      <USwitch
                        v-model="atendimentoRN"
                        :disabled="!podeEditar"
                      />
                    </div>
                  </UFormField>
                </div>

                <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <UFormField label="Tipo de internação">
                    <USelectMenu
                      v-model="tipoInternacao"
                      :items="tiposInternacao"
                      placeholder="Selecione o tipo"
                      :disabled="!podeEditar"
                      class="w-full"
                    />
                  </UFormField>

                  <UFormField label="Regime de internação">
                    <USelectMenu
                      v-model="regimeInternacao"
                      :items="regimesInternacao"
                      placeholder="Selecione o regime"
                      :disabled="!podeEditar"
                      class="w-full"
                    />
                  </UFormField>

                  <UFormField label="Quantidade de diárias solicitadas">
                    <UInput
                      v-model="quantidadeDiarias"
                      type="number"
                      min="1"
                      placeholder="1"
                      :default-value="1"
                      :disabled="!podeEditar"
                      class="w-full"
                    />
                  </UFormField>
                </div>

                <UFormField label="Indicação clínica">
                  <UTextarea
                    v-model="indicacaoClinica"
                    placeholder="Descreva a indicação clínica..."
                    :rows="6"
                    :disabled="!podeEditar"
                    class="w-full"
                  />
                </UFormField>

                <UFormField label="Diagnósticos (CID-10)">
                  <div class="flex flex-col gap-2 sm:flex-row">
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
                      :disabled="!podeEditar || cidSelecionadoLista.length >= MAX_CIDS"
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
                      aria-label="Adicionar CID"
                      color="primary"
                      :disabled="!podeEditar || !cidTempSelecionado || cidSelecionadoLista.length >= MAX_CIDS"
                      @click="adicionarCid(cidTempSelecionado!); cidTempSelecionado = null"
                    />
                  </div>

                  <div
                    v-if="cidSelecionadoLista.length"
                    class="mt-3 space-y-2"
                  >
                    <div
                      v-for="(cid, posicao) in cidSelecionadoLista"
                      :key="cid.cid"
                      class="flex items-start justify-between gap-2 rounded-lg border border-muted p-2"
                    >
                      <span class="text-sm">
                        {{ cid.cid }} — {{ cid.nome }}
                        <UBadge
                          v-if="posicao === 0"
                          size="xs"
                          color="primary"
                          variant="soft"
                        >Principal</UBadge>
                      </span>
                      <UButton
                        v-if="podeEditar"
                        icon="i-lucide-x"
                        :aria-label="`Remover CID ${cid.cid}`"
                        size="xs"
                        color="error"
                        variant="ghost"
                        @click="removerCid(posicao)"
                      />
                    </div>
                  </div>
                  <p
                    v-else
                    class="text-sm text-muted italic mt-3 text-center"
                  >
                    Nenhum CID selecionado
                  </p>
                  <p
                    class="text-xs text-muted mt-2"
                  >
                    Máximo de {{ MAX_CIDS }} CIDs (principal + secundários)
                  </p>
                </UFormField>
              </UCard>
            </div>
            <div
              v-if="index === 1"
              class="space-y-4 p-4 sm:p-6"
            >
              <UFormField label="OPME solicitados">
                <div class="flex flex-col gap-2 sm:flex-row">
                  <UInput
                    v-model="opmeCodigo"
                    placeholder="Código OPM"
                    :disabled="!podeEditar"
                    class="w-full sm:w-40"
                  />
                  <UInput
                    v-model="opmeNome"
                    placeholder="Descrição do material..."
                    icon="i-lucide-package"
                    :disabled="!podeEditar"
                    class="flex-1"
                  />
                  <UInput
                    v-model="opmeQuantidade"
                    type="number"
                    min="1"
                    placeholder="Qtd"
                    :default-value="1"
                    :disabled="!podeEditar"
                    class="w-full sm:w-24"
                  />
                  <UButton
                    icon="i-lucide-plus"
                    label="Adicionar"
                    color="primary"
                    variant="soft"
                    :disabled="!podeEditar || !opmeNome.trim()"
                    @click="adicionarOpme"
                  />
                </div>
              </UFormField>

              <UCard :ui="{ body: 'p-3' }">
                <template #title>
                  <div class="flex items-center justify-between">
                    <span class="text-sm font-medium">OPME selecionadas</span>
                    <span class="text-xs text-muted">{{ opmeItens.length }} item(ns)</span>
                  </div>
                </template>

                <div
                  v-if="opmeItens.length"
                  class="space-y-2"
                >
                  <div
                    v-for="(opme, posicao) in opmeItens"
                    :key="`${opme.codigo}-${opme.nome}-${posicao}`"
                    class="flex flex-col items-stretch justify-between gap-3 rounded-lg border border-muted p-3 sm:flex-row sm:items-start"
                  >
                    <div class="min-w-0 space-y-1">
                      <p class="text-sm font-medium truncate">
                        <span
                          v-if="opme.codigo"
                          class="font-mono text-primary"
                        >{{ opme.codigo }} — </span>{{ opme.nome }}
                      </p>
                      <UBadge
                        size="xs"
                        color="neutral"
                        variant="soft"
                      >
                        Qtd: {{ opme.quantidade }}
                      </UBadge>
                    </div>
                    <UButton
                      v-if="podeEditar"
                      icon="i-lucide-x"
                      :aria-label="`Remover OPME ${opme.nome}`"
                      color="error"
                      variant="ghost"
                      size="sm"
                      class="self-end sm:self-auto"
                      @click="removerOpme(posicao)"
                    />
                  </div>
                </div>
                <p
                  v-else
                  class="text-sm text-muted italic py-4 text-center"
                >
                  Nenhuma OPME selecionada.
                </p>
              </UCard>
            </div>
          </template>
        </UTabs>
      </div>
    </template>

    <template #footer>
      <div class="flex w-full flex-col-reverse gap-2 sm:flex-row sm:justify-between">
        <UButton
          label="Cancelar"
          color="neutral"
          variant="ghost"
          class="w-full justify-center sm:w-auto"
          @click="void (open = false)"
        />
        <UButton
          icon="i-lucide-printer"
          :label="botaoLabel"
          :disabled="!podeEnviar"
          :loading="salvando"
          class="w-full justify-center sm:w-auto"
          @click="salvarEImprimir"
        />
      </div>
    </template>
  </UModal>
</template>
