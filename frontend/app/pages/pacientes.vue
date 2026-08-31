<script setup lang="ts">
import type {
  AgendamentoComPaciente,
  AtestadoDocumentoDados,
  DocumentoMedico,
  DocumentoMedicoTipo,
  EncaminhamentoDocumentoDados,
  HistoricoLocalRecord,
  SolicitacaoOpmeDocumentoDados,
  SolicitacaoProcedimentoDocumentoDados
} from '~/types'
import { CalendarDate, DateFormatter, getLocalTimeZone } from '@internationalized/date'
import { usePdfMake } from '~/utils/pdf'
import {
  buildAtestado,
  buildAtestadoComparecimento,
  buildEncaminhamento,
  buildReceita,
  buildSolicitacaoExames,
  buildSolicitacaoOpme,
  buildSolicitacaoProcedimento
} from '~/utils/pdf-documents'
import { gerarHtmlGuiaInternacao, gerarHtmlGuiaOpme, gerarHtmlGuiaTiss, imprimirGuiaInternacao, imprimirGuiaOpme, imprimirGuiaTiss } from '~/utils/guia-tiss'

const openNav = inject<() => void>('openNav', () => {})
const auth = useAuthStore()

const df = new DateFormatter('pt-BR', {
  dateStyle: 'medium'
})

function hojeComoCalendarDate() {
  const d = new Date()
  return new CalendarDate(d.getFullYear(), d.getMonth() + 1, d.getDate())
}

function normalizarOpmeItens(dados: SolicitacaoOpmeDocumentoDados): { codigo?: string, nome: string, quantidade?: number }[] {
  const bruto = dados.opmeItens ?? (typeof dados.opmeSolicitados === 'string'
    ? dados.opmeSolicitados.split(/\r?\n/).map(linha => linha.replace(/^[-•\s]+/, '').trim()).filter(Boolean).map(nome => ({ nome }))
    : [])

  const itens = Array.isArray(bruto)
    ? bruto
    : bruto
      ? [bruto]
      : []

  const opmes: { codigo?: string, nome: string, quantidade?: number }[] = []
  const nomes = new Set<string>()

  for (const item of itens) {
    if (typeof item === 'string') continue
    const nome = String((item as Record<string, unknown>).nome ?? '').trim()
    if (!nome) continue

    const chave = nome.toLocaleLowerCase('pt-BR')
    if (nomes.has(chave)) continue
    nomes.add(chave)

    opmes.push({
      codigo: String((item as Record<string, unknown>).codigo ?? '').trim() || undefined,
      nome,
      quantidade: Number((item as Record<string, unknown>).quantidade ?? 1) || 1
    })
  }

  return opmes
}

const buscaNome = ref('')
const filtroData = shallowRef(hojeComoCalendarDate())
const isLoading = ref(false)

const todosAgendamentos = ref<AgendamentoComPaciente[]>([])
const historicoLocalPorAgendamento = shallowRef<Record<string, HistoricoLocalRecord[]>>({})
const documentosDisponiveisPorAgendamento = ref<Record<string, { exames: boolean, receita: boolean }>>({})
const documentosMedicosPorAgendamento = shallowRef<Record<string, Partial<Record<DocumentoMedicoTipo, DocumentoMedico>>>>({})

const showAtestadoModal = ref(false)
const showEncaminhamentoModal = ref(false)
const showProcedimentoModal = ref(false)
const showOpmeModal = ref(false)
const showHistoricoSlideover = ref(false)
const dropdownAcoesAbertoId = ref<number | null>(null)

const agendamentoSelecionado = ref<AgendamentoComPaciente | null>(null)
const pacienteSelecionado = computed(() => agendamentoSelecionado.value?.paciente ?? undefined)

const temBuscaNome = computed(() => buscaNome.value.trim().length > 0)
let disponibilidadeRequestId = 0
let documentosMedicosRequestId = 0

const agendamentosFiltrados = computed(() => {
  let lista = todosAgendamentos.value.filter(a => a.status === 'atendido')

  if (temBuscaNome.value) {
    const termo = buscaNome.value.trim().toLowerCase()
    lista = lista.filter(a => a.paciente.nome.toLowerCase().includes(termo))
  }

  if (!temBuscaNome.value && filtroData.value) {
    lista = lista.filter(a => a.data === filtroData.value.toString())
  }

  return lista.sort((a, b) => b.data.localeCompare(a.data) || b.horario.localeCompare(a.horario))
})

onMounted(async () => {
  await carregarAgendamentos()
})

async function carregarAgendamentos() {
  isLoading.value = true
  try {
    const params = new URLSearchParams()
    params.set('status', 'atendido')
    if (temBuscaNome.value) {
      params.set('search', buscaNome.value.trim())
    } else if (filtroData.value) {
      params.set('data', filtroData.value.toString())
    }
    const qs = params.toString()

    const raw = await $fetch<(AgendamentoComPaciente | Record<string, unknown>)[]>(`/api/agendamentos${qs ? `?${qs}` : ''}`)

    const comPaciente = (raw as AgendamentoComPaciente[]).filter(a => 'paciente' in a)

    todosAgendamentos.value = comPaciente
    void carregarDisponibilidadeDocumentos(comPaciente)
    void carregarDocumentosMedicos(comPaciente)
  } catch {
    console.error('Erro ao carregar agendamentos')
  } finally {
    isLoading.value = false
  }
}

watch(filtroData, () => {
  void carregarAgendamentos()
})

let debounceTimer: ReturnType<typeof setTimeout> | null = null

watch(buscaNome, () => {
  if (debounceTimer) clearTimeout(debounceTimer)
  debounceTimer = setTimeout(() => {
    void carregarAgendamentos()
  }, 400)
})

function calcularIdade(dataNascimento: string) {
  const hoje = new Date()
  const nasc = new Date(dataNascimento)
  let idade = hoje.getFullYear() - nasc.getFullYear()
  const mes = hoje.getMonth() - nasc.getMonth()
  if (mes < 0 || (mes === 0 && hoje.getDate() < nasc.getDate())) idade--
  return idade
}

function formatarDataPtBR(dataISO: string) {
  if (!dataISO) return ''
  return new Date(dataISO + 'T12:00:00').toLocaleDateString('pt-BR')
}

function abrirHistorico(ag: AgendamentoComPaciente) {
  agendamentoSelecionado.value = ag
  showHistoricoSlideover.value = true
}

function setDropdownAcoesAberto(agendamentoId: number, aberto: boolean) {
  dropdownAcoesAbertoId.value = aberto ? agendamentoId : null
}

function executarAcaoDropdown(acao: () => void | Promise<void>) {
  dropdownAcoesAbertoId.value = null
  void nextTick().then(() => {
    void acao()
  })
}

function hojeIso() {
  const d = new Date()
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}

function atendimentoEhHoje(ag: AgendamentoComPaciente) {
  return ag.data === hojeIso()
}

function documentoMedico(ag: AgendamentoComPaciente | null, tipo: DocumentoMedicoTipo) {
  if (!ag) return null
  return documentosMedicosPorAgendamento.value[String(ag.id)]?.[tipo] ?? null
}

const documentoAtestadoSelecionado = computed(() => documentoMedico(agendamentoSelecionado.value, 'ATESTADO'))
const documentoEncaminhamentoSelecionado = computed(() => documentoMedico(agendamentoSelecionado.value, 'ENCAMINHAMENTO'))
const documentoProcedimentoSelecionado = computed(() => documentoMedico(agendamentoSelecionado.value, 'SOLICITACAO_PROCEDIMENTO'))
const documentoOpmeSelecionado = computed(() => documentoMedico(agendamentoSelecionado.value, 'SOLICITACAO_OPME'))

function atualizarDocumentoMedico(documento: DocumentoMedico) {
  const chave = String(documento.medSpdataAtendimentoId)
  documentosMedicosPorAgendamento.value = {
    ...documentosMedicosPorAgendamento.value,
    [chave]: {
      ...documentosMedicosPorAgendamento.value[chave],
      [documento.tipoDocumento]: documento
    }
  }
}

async function abrirDocumentoMedico(ag: AgendamentoComPaciente, tipo: DocumentoMedicoTipo) {
  agendamentoSelecionado.value = ag
  const documento = documentoMedico(ag, tipo)

  if (!atendimentoEhHoje(ag)) {
    if (documento) await imprimirDocumentoMedico(ag, documento)
    return
  }

  if (tipo === 'ATESTADO') showAtestadoModal.value = true
  if (tipo === 'ENCAMINHAMENTO') showEncaminhamentoModal.value = true
  if (tipo === 'SOLICITACAO_PROCEDIMENTO') showProcedimentoModal.value = true
  if (tipo === 'SOLICITACAO_OPME') showOpmeModal.value = true
}

function formatarDataParaPdf(dataISO: string) {
  if (!dataISO) return ''
  return new Date(dataISO + 'T12:00:00').toLocaleDateString('pt-BR')
}

function chaveAgendamento(ag: AgendamentoComPaciente) {
  return [ag.spdataAtendimentoId || ag.id, ag.paciente.id, ag.data].join(':')
}

async function buscarHistoricoLocal(ag: AgendamentoComPaciente): Promise<HistoricoLocalRecord[]> {
  const chave = chaveAgendamento(ag)
  const cached = historicoLocalPorAgendamento.value[chave]
  if (cached) return cached

  try {
    const historico = await $fetch<HistoricoLocalRecord[]>(`/api/historico-local/${ag.paciente.id}`, {
      query: {
        cpf: ag.paciente.cpf || undefined,
        nome: ag.paciente.nome || undefined,
        spdataAtendimentoId: ag.spdataAtendimentoId || undefined,
        data: ag.data
      }
    })
    historicoLocalPorAgendamento.value = {
      ...historicoLocalPorAgendamento.value,
      [chave]: historico
    }
    return historico
  } catch {
    return []
  }
}

function encontrarRegistroPorData(historico: HistoricoLocalRecord[], dataISO: string): HistoricoLocalRecord | null {
  const registro = historico.find((h) => {
    if (!h.data_consulta) return false
    const dataHist = h.data_consulta.split('T')[0]
    return dataHist === dataISO
  })
  if (registro) return registro
  return null
}

function registroTemExames(registro: HistoricoLocalRecord | null) {
  return Boolean(registro?.exames?.some((e) => {
    if (typeof e === 'string') return e.trim().length > 0
    return Boolean(e.nome || e.descricao || e.tipo_exame)
  }))
}

function registroTemReceita(registro: HistoricoLocalRecord | null) {
  return Boolean(registro?.medicamentos?.some(m => m.trim().length > 0))
}

function calcularDocumentosDisponiveis(ag: AgendamentoComPaciente, historico: HistoricoLocalRecord[]) {
  const registro = encontrarRegistroPorData(historico, ag.data)
  return {
    exames: registroTemExames(registro),
    receita: registroTemReceita(registro)
  }
}

function documentosDisponiveis(ag: AgendamentoComPaciente) {
  return documentosDisponiveisPorAgendamento.value[chaveAgendamento(ag)] ?? { exames: false, receita: false }
}

async function carregarDisponibilidadeDocumentos(agendamentos: AgendamentoComPaciente[]) {
  const requestId = ++disponibilidadeRequestId

  await Promise.all(agendamentos.map(async (ag) => {
    const historico = await buscarHistoricoLocal(ag)
    if (requestId !== disponibilidadeRequestId) return

    const chave = chaveAgendamento(ag)
    documentosDisponiveisPorAgendamento.value = {
      ...documentosDisponiveisPorAgendamento.value,
      [chave]: calcularDocumentosDisponiveis(ag, historico)
    }
  }))
}

async function carregarDocumentosMedicos(agendamentos: AgendamentoComPaciente[]) {
  const requestId = ++documentosMedicosRequestId
  const ids = Array.from(new Set(agendamentos.map(a => a.id).filter(id => Number.isFinite(id))))

  if (!ids.length) return

  try {
    const documentos = await $fetch<DocumentoMedico[]>('/api/documentos-medicos', {
      query: { ids: ids.join(',') }
    })

    if (requestId !== documentosMedicosRequestId) return

    const porAgendamento = { ...documentosMedicosPorAgendamento.value }
    for (const id of ids) porAgendamento[String(id)] = {}

    for (const documento of documentos) {
      const chave = String(documento.medSpdataAtendimentoId)
      porAgendamento[chave] = {
        ...porAgendamento[chave],
        [documento.tipoDocumento]: documento
      }
    }

    documentosMedicosPorAgendamento.value = porAgendamento
  } catch {
    console.error('Erro ao carregar documentos médicos')
  }
}

const TEXTO_ATESTADO = `Atesto que o(a) paciente {nome} esteve sob meus cuidados médicos, necessitando de {dias} dias de repouso/afastamento a partir de {data}.`

function textoAtestado(paciente: string, dados: AtestadoDocumentoDados) {
  return TEXTO_ATESTADO
    .replace('{nome}', paciente)
    .replace('{dias}', String(dados.dias_afastamento))
    .replace('{data}', formatarDataParaPdf(dados.data_inicio))
}

async function imprimirDocumentoMedico(ag: AgendamentoComPaciente, documento: DocumentoMedico) {
  const pdfMake = await usePdfMake()
  const convenio = (ag.paciente.convenio ?? '').toLowerCase().trim()
  const convenioNaoParticular = Boolean(convenio && convenio !== 'particular')

  if (documento.tipoDocumento === 'ATESTADO') {
    const dados = documento.dados as AtestadoDocumentoDados
    const doc = await buildAtestado({
      paciente: ag.paciente.nome,
      conteudoHtml: `<p>${textoAtestado(ag.paciente.nome, dados)}</p>`,
      medico: dados.medico ?? undefined,
      crm: dados.crm ?? undefined,
      especialidade: dados.especialidade ?? undefined
    })
    pdfMake.createPdf(doc).open()
    return
  }

  if (documento.tipoDocumento === 'ENCAMINHAMENTO') {
    const dados = documento.dados as EncaminhamentoDocumentoDados
    const doc = await buildEncaminhamento({
      paciente: ag.paciente.nome,
      data: formatarDataParaPdf(dados.data),
      encaminharPara: dados.encaminhar_para,
      profissionalExterno: dados.profissional_externo,
      medico: dados.medico ?? undefined,
      crm: dados.crm ?? undefined,
      especialidade: dados.especialidade ?? undefined
    })
    pdfMake.createPdf(doc).open()
    return
  }

  if (documento.tipoDocumento === 'SOLICITACAO_OPME') {
    const dados = documento.dados as SolicitacaoOpmeDocumentoDados
    const dataFormatada = formatarDataParaPdf(dados.data)
    const opmeItens = normalizarOpmeItens(dados)

    if (convenioNaoParticular) {
      const html = await gerarHtmlGuiaOpme({
        paciente: ag.paciente.nome,
        data: dataFormatada,
        convenio: ag.paciente.convenio,
        idConvenioSpdata: ag.paciente.idConvenioSpdata,
        medico: dados.medico ?? undefined,
        crm: dados.crm ?? undefined,
        especialidade: dados.especialidade ?? undefined,
        indicacaoClinica: dados.indicacaoClinica ?? '',
        opmeItens
      })
      imprimirGuiaOpme(html)
      return
    }

    const doc = await buildSolicitacaoOpme({
      paciente: ag.paciente.nome,
      data: dataFormatada,
      opmeItens,
      indicacaoClinica: dados.indicacaoClinica ?? undefined,
      medico: dados.medico ?? undefined,
      crm: dados.crm ?? undefined,
      especialidade: dados.especialidade ?? undefined
    })
    pdfMake.createPdf(doc).open()
    return
  }

  const dados = documento.dados as SolicitacaoProcedimentoDocumentoDados
  const dataFormatada = formatarDataParaPdf(dados.data)

  if (convenioNaoParticular) {
    const html = await gerarHtmlGuiaInternacao({
      paciente: ag.paciente.nome,
      data: dataFormatada,
      convenio: ag.paciente.convenio,
      idConvenioSpdata: ag.paciente.idConvenioSpdata,
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
      procedimentos: dados.procedimentos
    })
    imprimirGuiaInternacao(html)
    return
  }

  const doc = await buildSolicitacaoProcedimento({
    paciente: ag.paciente.nome,
    data: dataFormatada,
    descricao: dados.descricao,
    procedimentos: dados.procedimentos,
    medico: dados.medico ?? undefined,
    crm: dados.crm ?? undefined,
    especialidade: dados.especialidade ?? undefined
  })
  pdfMake.createPdf(doc).open()
}

async function gerarAtestadoComparecimento(ag: AgendamentoComPaciente) {
  const pdfMake = await usePdfMake()
  const doc = await buildAtestadoComparecimento({
    paciente: ag.paciente.nome,
    data: formatarDataParaPdf(ag.data),
    horario: ag.horario,
    medico: auth.user?.nome,
    crm: auth.user?.crm,
    especialidade: auth.user?.especialidades?.join(', ')
  })
  pdfMake.createPdf(doc).open()
}

async function gerarSolicitacaoExames(ag: AgendamentoComPaciente) {
  const historico = await buscarHistoricoLocal(ag)
  const registro = encontrarRegistroPorData(historico, ag.data)

  const exames = registro?.exames?.map((e) => {
    if (typeof e === 'string') return { nome: e, orientacao: null }
    return {
      nome: e.nome || e.descricao || '',
      codigo_amb: e.codigo_amb ?? null,
      codigo_alfanumerico: e.codigo_alfanumerico ?? null,
      orientacao: e.orientacao ?? null
    }
  }).filter(e => e.nome) ?? []

  if (exames.length === 0) {
    console.warn('Nenhum exame encontrado para esta consulta')
    return
  }

  const convenio = (ag.paciente.convenio ?? '').toLowerCase()

  if (convenio && convenio !== 'particular') {
    const params = {
      paciente: ag.paciente.nome,
      cpf: ag.paciente.cpf,
      convenio: ag.paciente.convenio ?? '',
      idConvenioSpdata: ag.paciente.idConvenioSpdata,
      data: formatarDataParaPdf(ag.data),
      exames,
      medico: auth.user?.nome,
      crm: auth.user?.crm,
      especialidade: auth.user?.especialidades?.join(', ')
    }
    const html = await gerarHtmlGuiaTiss(params)
    imprimirGuiaTiss(html)
    return
  }

  const pdfMake = await usePdfMake()
  const doc = await buildSolicitacaoExames({
    paciente: ag.paciente.nome,
    data: formatarDataParaPdf(ag.data),
    exames,
    medico: auth.user?.nome,
    crm: auth.user?.crm,
    especialidade: auth.user?.especialidades?.join(', ')
  })
  pdfMake.createPdf(doc).open()
}

async function gerarReceita(ag: AgendamentoComPaciente) {
  const historico = await buscarHistoricoLocal(ag)
  const registro = encontrarRegistroPorData(historico, ag.data)

  const medicamentos = registro?.medicamentos?.join('\n') ?? ''

  if (!medicamentos) {
    console.warn('Nenhum medicamento encontrado para esta consulta')
    return
  }

  const pdfMake = await usePdfMake()
  const doc = await buildReceita({
    paciente: ag.paciente.nome,
    data: formatarDataParaPdf(ag.data),
    medicamentos: [],
    texto: medicamentos,
    medico: auth.user?.nome,
    crm: auth.user?.crm,
    especialidade: auth.user?.especialidades?.join(', ')
  })
  pdfMake.createPdf(doc).open()
}

type DropdownItem = {
  label: string
  icon: string
  onSelect: () => void
}

function itemDocumentoMedico(ag: AgendamentoComPaciente, tipo: DocumentoMedicoTipo, label: string, icon: string): DropdownItem | null {
  const documento = documentoMedico(ag, tipo)
  const podeCriarOuEditar = atendimentoEhHoje(ag)

  if (!podeCriarOuEditar && !documento) return null

  return {
    label: podeCriarOuEditar ? label : `Imprimir ${label}`,
    icon,
    onSelect: () => {
      executarAcaoDropdown(() => abrirDocumentoMedico(ag, tipo))
    }
  }
}

function dropdownItems(ag: AgendamentoComPaciente) {
  const docs = documentosDisponiveis(ag)
  const documentosMedicos = [
    itemDocumentoMedico(ag, 'ATESTADO', 'Atestado Médico', 'i-lucide-file-text'),
    itemDocumentoMedico(ag, 'SOLICITACAO_PROCEDIMENTO', 'Solicitação de Procedimento', 'i-lucide-clipboard-list'),
    itemDocumentoMedico(ag, 'SOLICITACAO_OPME', 'Solicitação de OPME', 'i-lucide-sliders-horizontal'),
    itemDocumentoMedico(ag, 'ENCAMINHAMENTO', 'Encaminhamento Médico', 'i-lucide-arrow-right-circle')
  ].filter((item): item is DropdownItem => Boolean(item))

  return [
    [
      ...documentosMedicos,
      { label: 'Atestado de Comparecimento', icon: 'i-lucide-calendar-check', onSelect: () => executarAcaoDropdown(() => gerarAtestadoComparecimento(ag)) },
      ...(docs.exames ? [{ label: 'Solicitação de Exames', icon: 'i-lucide-flask-conical', onSelect: () => executarAcaoDropdown(() => gerarSolicitacaoExames(ag)) }] : []),
      ...(docs.receita ? [{ label: 'Receita Médica', icon: 'i-lucide-pill', onSelect: () => executarAcaoDropdown(() => gerarReceita(ag)) }] : [])
    ]
  ]
}
</script>

<template>
  <div>
    <UHeader
      title="Meus Pacientes"
      toggle-side="left"
    >
      <template #toggle>
        <UButton
          icon="i-lucide-panel-left"
          color="neutral"
          variant="ghost"
          class="lg:hidden"
          aria-label="Abrir menu"
          @click="openNav()"
        />
      </template>
    </UHeader>
    <div class="min-h-screen min-w-0 space-y-6 bg-neutral-100 p-3 dark:bg-neutral-950 sm:p-6">
      <div class="flex flex-col sm:flex-row gap-3">
        <UInput
          v-model="buscaNome"
          icon="i-lucide-search"
          placeholder="Buscar por nome do paciente..."
          class="flex-1"
          :ui="{ root: 'w-full' }"
        />
        <UPopover>
          <UButton
            color="neutral"
            variant="subtle"
            icon="i-lucide-calendar"
            class="min-h-10 w-full justify-center whitespace-normal sm:w-auto"
          >
            {{ filtroData ? df.format(filtroData.toDate(getLocalTimeZone())) : 'Select a date' }}
          </UButton>

          <template #content>
            <UCalendar
              v-model="filtroData"
              class="p-2"
            />
          </template>
        </UPopover>
      </div>

      <div
        v-if="isLoading"
        class="flex justify-center py-12"
      >
        <UIcon
          name="i-lucide-loader-circle"
          class="size-8 animate-spin text-muted"
        />
      </div>

      <div
        v-else-if="agendamentosFiltrados.length === 0"
        class="flex flex-col items-center py-16 gap-3 text-center"
      >
        <p class="text-lg font-medium text-muted">
          Nenhum paciente encontrado
        </p>
        <p class="text-sm text-muted">
          {{ temBuscaNome ? 'Tente buscar com outro nome.' : 'Nenhum paciente atendido nesta data.' }}
        </p>
      </div>

      <div
        v-else
        class="space-y-3"
      >
        <UCard
          v-for="ag in agendamentosFiltrados"
          :key="ag.id"
          class="border border-muted"
          :ui="{ body: 'p-4 sm:p-4' }"
        >
          <div class="flex min-w-0 flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
            <div class="flex min-w-0 items-center w-full gap-4">
              <UAvatar
                :alt="ag.paciente.nome"
                color="primary"
                size="lg"
                class="shrink-0"
              />

              <div class="min-w-0 w-full">
                <div class="flex min-w-0 flex-col gap-1 sm:flex-row sm:items-center sm:justify-between">
                  <p class="font-semibold text-base text-default truncate">
                    {{ ag.paciente.nome }}
                  </p>

                  <span class="flex shrink-0 items-center gap-1 text-sm font-semibold sm:text-base">
                    <UIcon
                      name="i-lucide-calendar"
                      class="size-4"
                    />
                    {{ formatarDataPtBR(ag.data) }} · {{ ag.horario }}
                  </span>
                </div>

                <p class="break-words text-sm text-muted">
                  {{ calcularIdade(ag.paciente.dataNascimento) }} anos · {{ ag.paciente.convenio }}
                </p>

                <div class="mt-2 flex flex-wrap gap-x-4 gap-y-1 text-xs text-muted">
                  <span
                    v-if="ag.paciente.telefone"
                    class="inline-flex min-w-0 items-center gap-1 break-all"
                  >
                    <UIcon
                      name="i-lucide-phone"
                      class="size-3"
                    />
                    {{ ag.paciente.telefone }}
                  </span>
                  <span
                    v-if="ag.paciente.email"
                    class="inline-flex items-center gap-1"
                  >
                    <UIcon
                      name="i-lucide-mail"
                      class="size-3"
                    />
                    {{ ag.paciente.email }}
                  </span>
                </div>
              </div>
            </div>

            <div class="grid grid-cols-2 gap-2 sm:flex sm:justify-end">
              <UButton
                icon="i-lucide-clock"
                label="Histórico"
                color="neutral"
                variant="outline"
                size="sm"
                class="min-h-10 justify-center"
                @click="abrirHistorico(ag)"
              />
              <UDropdownMenu
                :items="dropdownItems(ag)"
                :open="dropdownAcoesAbertoId === ag.id"
                :modal="false"
                :ui="{ content: 'w-56' }"
                @update:open="setDropdownAcoesAberto(ag.id, $event)"
              >
                <UButton
                  label="Ações"
                  icon="i-lucide-chevron-down"
                  color="primary"
                  variant="outline"
                  size="sm"
                  class="min-h-10 justify-center"
                />
              </UDropdownMenu>
            </div>
          </div>
        </UCard>
      </div>
    </div>

    <AtestadoGerarModal
      v-model:open="showAtestadoModal"
      :paciente="pacienteSelecionado"
      :agendamento="agendamentoSelecionado"
      :data-atendimento="agendamentoSelecionado?.data"
      :documento="documentoAtestadoSelecionado"
      @saved="atualizarDocumentoMedico"
    />
    <EncaminhamentoGerarModal
      v-model:open="showEncaminhamentoModal"
      :paciente="pacienteSelecionado"
      :agendamento="agendamentoSelecionado"
      :data-atendimento="agendamentoSelecionado?.data"
      :documento="documentoEncaminhamentoSelecionado"
      @saved="atualizarDocumentoMedico"
    />
    <ProcedimentoGerarModal
      v-model:open="showProcedimentoModal"
      :paciente="pacienteSelecionado"
      :agendamento="agendamentoSelecionado"
      :data-atendimento="agendamentoSelecionado?.data"
      :documento="documentoProcedimentoSelecionado"
      @saved="atualizarDocumentoMedico"
    />
    <ProcedimentoGerarModal
      v-model:open="showOpmeModal"
      :paciente="pacienteSelecionado"
      :agendamento="agendamentoSelecionado"
      :data-atendimento="agendamentoSelecionado?.data"
      :documento="documentoOpmeSelecionado"
      aba-inicial="opme"
      @saved="atualizarDocumentoMedico"
    />
    <HistoricoSlideover
      v-model:open="showHistoricoSlideover"
      :paciente="pacienteSelecionado"
      :agendamento="agendamentoSelecionado"
    />
  </div>
</template>
