<script setup lang="ts">
import type { DropdownMenuItem } from '@nuxt/ui/'

const openNav = inject<() => void>('openNav', () => {})
const auth = useAuthStore()

interface ExameRetencao {
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

interface RetencaoExamesResponse {
  items: ExameRetencao[]
  dataIni: string
  dataFim: string
}

interface ContatoRetencao {
  data: string
  canal: string
  usuario: string
  resultado: string
  observacao: string
}

const examesRetencao = ref<ExameRetencao[]>([])
const loading = ref(false)
const errorMsg = ref('')

const hoje = new Date()
const anoAtual = String(hoje.getFullYear())
const mesesOpcoes = ['Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho', 'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro']
const mesAtualNome = mesesOpcoes[hoje.getMonth()] || 'Janeiro'

const MES_PARA_NUMERO: Record<string, string> = {
  Janeiro: '01', Fevereiro: '02', Março: '03', Abril: '04',
  Maio: '05', Junho: '06', Julho: '07', Agosto: '08',
  Setembro: '09', Outubro: '10', Novembro: '11', Dezembro: '12'
}

const filtroAno = ref(anoAtual)
const filtroMesInicio = ref(mesAtualNome)
const filtroMesFim = ref(mesAtualNome)
const filtroMedico = ref('Todos')
const filtroEspecialidade = ref('Todos')
const filtroConvenio = ref('Todos')
const filtroStatus = ref('Todos')
const filtroExame = ref('')
const filtroPaciente = ref('')

const filtroAnoActive = ref(anoAtual)
const filtroMesInicioActive = ref(mesAtualNome)
const filtroMesFimActive = ref(mesAtualNome)
const filtroMedicoActive = ref('Todos')
const filtroEspecialidadeActive = ref('Todos')
const filtroConvenioActive = ref('Todos')
const filtroStatusActive = ref('Todos')

const filtroPeriodoInicioActive = computed(() => `${filtroAnoActive.value}-${MES_PARA_NUMERO[filtroMesInicioActive.value]}`)
const filtroPeriodoFimActive = computed(() => `${filtroAnoActive.value}-${MES_PARA_NUMERO[filtroMesFimActive.value]}`)

function ultimoDiaMes(ano: string, mes: string) {
  return new Date(Number(ano), Number(MES_PARA_NUMERO[mes] || '01'), 0).getDate()
}

function dataInicioFiltro() {
  return `${filtroAnoActive.value}-${MES_PARA_NUMERO[filtroMesInicioActive.value] || '01'}-01`
}

function dataFimFiltro() {
  const mes = MES_PARA_NUMERO[filtroMesFimActive.value] || '01'
  return `${filtroAnoActive.value}-${mes}-${String(ultimoDiaMes(filtroAnoActive.value, filtroMesFimActive.value)).padStart(2, '0')}`
}

async function carregarRetencao() {
  const unidadeId = auth.activeClinicaId
  loading.value = true
  errorMsg.value = ''

  if (!unidadeId) {
    examesRetencao.value = []
    errorMsg.value = 'Selecione uma unidade para carregar conversão de exames'
    loading.value = false
    return
  }

  const params = new URLSearchParams()
  params.set('dataIni', dataInicioFiltro())
  params.set('dataFim', dataFimFiltro())
  params.set('unidadeId', String(unidadeId))

  try {
    const response = await $fetch<RetencaoExamesResponse>(`/api/retencao-exames?${params.toString()}`)
    examesRetencao.value = response.items
  } catch {
    examesRetencao.value = []
    errorMsg.value = 'Erro ao carregar conversão de exames'
  } finally {
    loading.value = false
  }
}

function aplicarFiltros() {
  filtroAnoActive.value = filtroAno.value
  filtroMesInicioActive.value = filtroMesInicio.value
  filtroMesFimActive.value = filtroMesFim.value
  filtroMedicoActive.value = filtroMedico.value
  filtroEspecialidadeActive.value = filtroEspecialidade.value
  filtroConvenioActive.value = filtroConvenio.value
  filtroStatusActive.value = filtroStatus.value
  page.value = 1
  carregarRetencao()
}

function opcaoFiltro(valor: string | null | undefined) {
  const texto = String(valor ?? '').trim()
  if (!texto || texto === '0') return ''
  return texto
}

function montarOpcoesFiltro(opcoes: string[]) {
  const itens = [...new Set(opcoes.map(opcaoFiltro).filter(Boolean))]
  return ['Todos', ...itens.sort((a, b) => a.localeCompare(b, 'pt-BR'))]
}

const medicosDisponiveis = computed(() => {
  return montarOpcoesFiltro(examesRetencao.value.map(e => e.medico))
})

const especialidadesDisponiveis = computed(() => {
  return montarOpcoesFiltro(examesRetencao.value.map(e => e.especialidade))
})

const conveniosDisponiveis = computed(() => {
  return montarOpcoesFiltro(examesRetencao.value.map(e => e.convenio))
})

const STATUS_VALUE_MAP: Record<string, string> = {
  'Todos': 'Todos',
  'Pendente': 'pendente',
  'Realizado': 'realizado',
  'Não Convertido': 'nao-convertido'
}

const statusDisponiveis = ['Todos', 'Pendente', 'Realizado', 'Não Convertido']
const STATUS_EM_ABERTO = new Set<ExameRetencao['status']>(['pendente'])

const dadosFiltrados = computed(() => {
  return examesRetencao.value.filter((e) => {
    if (filtroMedicoActive.value !== 'Todos' && e.medico !== filtroMedicoActive.value) return false
    if (filtroEspecialidadeActive.value !== 'Todos' && e.especialidade !== filtroEspecialidadeActive.value) return false
    if (filtroConvenioActive.value !== 'Todos' && e.convenio !== filtroConvenioActive.value) return false
    if (filtroStatusActive.value !== 'Todos' && e.status !== STATUS_VALUE_MAP[filtroStatusActive.value]) return false
    if (e.dataSolicitacao.substring(0, 7) < filtroPeriodoInicioActive.value) return false
    if (e.dataSolicitacao.substring(0, 7) > filtroPeriodoFimActive.value) return false
    return true
  })
})

const pacientesVisiveis = computed(() => {
  let lista = dadosFiltrados.value
  const termoExame = filtroExame.value.toLowerCase().trim()
  const termoPaciente = filtroPaciente.value.toLowerCase().trim()
  if (termoExame) {
    lista = lista.filter(e => e.exame.toLowerCase().includes(termoExame) || e.codigoTuss.includes(termoExame))
  }
  if (termoPaciente) {
    lista = lista.filter(e => e.paciente.toLowerCase().includes(termoPaciente) || e.cpf.includes(termoPaciente) || e.prontuario.toLowerCase().includes(termoPaciente))
  }
  return lista
})

const totalExamesSolicitados = computed(() => dadosFiltrados.value.length)
const totalRealizadosInternamente = computed(() => dadosFiltrados.value.filter(e => e.status === 'realizado').length)
const totalPendentes = computed(() => dadosFiltrados.value.filter(e => STATUS_EM_ABERTO.has(e.status)).length)
const totalNaoConvertidos = computed(() => dadosFiltrados.value.filter(e => e.status === 'nao-convertido').length)
const taxaConversao = computed(() => {
  const total = dadosFiltrados.value.length
  const realizados = dadosFiltrados.value.filter(e => e.status === 'realizado').length
  return total > 0 ? Math.round((realizados / total) * 100) : 0
})
const faturamentoRealizado = computed(() => {
  return dadosFiltrados.value
    .filter(e => e.status === 'realizado' && e.valorRealizado)
    .reduce((acc, e) => acc + (e.valorRealizado || 0), 0)
})
const page = ref(1)
const pageSize = 8

const pacientesPaginados = computed(() => {
  const inicio = (page.value - 1) * pageSize
  return pacientesVisiveis.value.slice(inicio, inicio + pageSize)
})

function corStatus(status: string) {
  switch (status) {
    case 'pendente': return 'warning'
    case 'realizado': return 'success'
    case 'nao-convertido': return 'error'
    default: return 'neutral'
  }
}

function rotuloStatus(status: string) {
  switch (status) {
    case 'pendente': return 'Pendente'
    case 'realizado': return 'Realizado'
    case 'nao-convertido': return 'Não Convertido'
    default: return status
  }
}

function formatarData(iso: string | null | undefined) {
  if (!iso) return '-'
  const [ano, mes, dia] = iso.split('-')
  if (!ano || !mes || !dia) return iso
  return `${dia}/${mes}/${ano}`
}

function formatarMoeda(valor: number | null) {
  if (valor === null || valor === undefined) return '-'
  return `R$ ${valor.toLocaleString('pt-BR')}`
}

const pacienteSelecionado = ref<ExameRetencao | null>(null)
const slideoverAberto = ref(false)

const examesPacienteSelecionado = computed(() => {
  const paciente = pacienteSelecionado.value
  if (!paciente) return []

  return examesRetencao.value.filter((exame) => {
    if (paciente.prontuario && exame.prontuario === paciente.prontuario) return true
    if (paciente.cpf && exame.cpf === paciente.cpf) return true
    return exame.id === paciente.id
  })
})

const historicoContato = computed<ContatoRetencao[]>(() => {
  const paciente = pacienteSelecionado.value
  if (!paciente?.ultimoContato) return []

  return [
    {
      data: paciente.ultimoContato,
      canal: 'Contato',
      usuario: paciente.responsavel || 'Responsável não informado',
      resultado: rotuloStatus(paciente.status),
      observacao: paciente.telefone ? `Telefone: ${paciente.telefone}` : ''
    }
  ]
})

function _abrirPaciente(item: ExameRetencao) {
  pacienteSelecionado.value = item
  slideoverAberto.value = true
}

function ligar(item: ExameRetencao) {
  const tel = item.telefone.replace(/\D/g, '')
  if (!tel) return
  window.location.href = `tel:${tel}`
}

function whatsapp(item: ExameRetencao) {
  const tel = item.telefone.replace(/\D/g, '')
  if (!tel) return
  window.open(`https://wa.me/55${tel}`, '_blank')
}

function agendar(item: ExameRetencao) {
  void item
}

function atualizarStatus(item: ExameRetencao, novoStatus: string) {
  const idx = examesRetencao.value.findIndex(e => e.id === item.id)
  if (idx >= 0) {
    examesRetencao.value[idx] = { ...examesRetencao.value[idx]!, status: novoStatus as ExameRetencao['status'] }
    pacienteSelecionado.value = examesRetencao.value[idx]!
  }
}

const itensAcoes = computed<DropdownMenuItem[][]>(() => {
  if (!pacienteSelecionado.value) return []
  return [
    [
      {
        label: 'WhatsApp',
        icon: 'i-lucide-message-circle',
        onSelect: () => whatsapp(pacienteSelecionado.value!)
      },
      {
        label: 'Ligar',
        icon: 'i-lucide-phone',
        onSelect: () => ligar(pacienteSelecionado.value!)
      },
      {
        label: 'Agendar',
        icon: 'i-lucide-calendar-plus',
        onSelect: () => agendar(pacienteSelecionado.value!)
      }
    ],
    [
      {
        label: 'Marcar como Realizado',
        icon: 'i-lucide-check-circle',
        onSelect: () => atualizarStatus(pacienteSelecionado.value!, 'realizado')
      },
      {
        label: 'Marcar como Pendente',
        icon: 'i-lucide-phone-off',
        onSelect: () => atualizarStatus(pacienteSelecionado.value!, 'pendente')
      },
      {
        label: 'Marcar como Não Convertido',
        icon: 'i-lucide-x-circle',
        onSelect: () => atualizarStatus(pacienteSelecionado.value!, 'nao-convertido')
      }
    ],
    [
      {
        label: 'Histórico Completo',
        icon: 'i-lucide-clock'
      }
    ]
  ]
})

const rankingExames = computed(() => {
  const totais = new Map<string, number>()

  for (const exame of dadosFiltrados.value) {
    const label = exame.exame || 'Exame não informado'
    totais.set(label, (totais.get(label) || 0) + 1)
  }

  return [...totais.entries()]
    .map(([exame, total]) => ({ exame, total }))
    .sort((a, b) => b.total - a.total)
    .slice(0, 10)
})

const rankingOportunidade = computed(() => {
  const totais = new Map<string, number>()

  for (const exame of dadosFiltrados.value) {
    if (!STATUS_EM_ABERTO.has(exame.status)) continue
    const label = exame.convenio || 'Convênio não informado'
    totais.set(label, (totais.get(label) || 0) + exame.valorEstimado)
  }

  return [...totais.entries()]
    .map(([convenio, valor]) => ({ convenio, valor }))
    .sort((a, b) => b.valor - a.valor)
    .slice(0, 10)
})

const rankingConversao = computed(() => {
  const totais = new Map<string, { medico: string, solicitados: number, realizados: number }>()

  for (const exame of dadosFiltrados.value) {
    const medico = exame.medico || 'Médico não informado'
    const atual = totais.get(medico) || { medico, solicitados: 0, realizados: 0 }
    atual.solicitados += 1
    if (exame.status === 'realizado') atual.realizados += 1
    totais.set(medico, atual)
  }

  return [...totais.values()]
    .map(item => ({
      medico: item.medico,
      taxa: item.solicitados ? Math.round((item.realizados / item.solicitados) * 100) : 0
    }))
    .sort((a, b) => b.taxa - a.taxa)
    .slice(0, 10)
})

const rankingEspecialidade = computed(() => {
  const totais = new Map<string, number>()

  for (const exame of dadosFiltrados.value) {
    const label = exame.especialidade || 'Especialidade não informada'
    totais.set(label, (totais.get(label) || 0) + 1)
  }

  return [...totais.entries()]
    .map(([label, total]) => ({ label, total }))
    .sort((a, b) => b.total - a.total)
    .slice(0, 10)
})

const chartExamesLabels = computed(() => rankingExames.value.map(e => e.exame))
const chartExamesDados = computed(() => rankingExames.value.map(e => e.total))

const chartOportunidadeLabels = computed(() => rankingOportunidade.value.map(o => o.convenio))
const chartOportunidadeDados = computed(() => rankingOportunidade.value.map(o => o.valor))

const chartConversaoMedicos = computed(() => rankingConversao.value.map(m => m.medico))
const chartConversaoTaxas = computed(() => rankingConversao.value.map(m => m.taxa))

const chartEspecialidadeLabels = computed(() => rankingEspecialidade.value.map(e => e.label))
const chartEspecialidadeDados = computed(() => rankingEspecialidade.value.map(e => e.total))

onMounted(() => {
  carregarRetencao()
})

watch(() => auth.activeClinicaId, () => {
  carregarRetencao()
})
</script>

<template>
  <div>
    <UHeader
      title="Conversão de Exames"
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
      <template #right>
        <div class="flex items-center gap-2">
          <UColorModeButton />
        </div>
      </template>
    </UHeader>
    <div class="min-h-screen min-w-0 space-y-6 bg-neutral-100 p-3 dark:bg-neutral-950 sm:space-y-8 sm:p-6">
      <UCard class="w-full">
        <template #title>
          <p class="text-lg font-medium">
            Filtros de Análise
          </p>
        </template>
        <div class="space-y-4">
          <div class="grid grid-cols-1 items-end gap-3 sm:grid-cols-2 xl:grid-cols-7 2xl:grid-cols-8">
            <div class="grid grid-cols-2 items-end gap-2 sm:col-span-2 xl:col-span-2 2xl:col-span-3 2xl:grid-cols-[6rem_1fr_auto_1fr]">
              <UFormField
                label="Ano"
                class="w-full"
              >
                <UInputMenu
                  v-model="filtroAno"
                  :items="[anoAtual, String(Number(anoAtual) - 1)]"
                  placeholder="Ano"
                  size="sm"
                  class="w-full"
                />
              </UFormField>
              <UFormField
                label="Mês início"
                class="w-full"
              >
                <UInputMenu
                  v-model="filtroMesInicio"
                  :items="mesesOpcoes"
                  placeholder="Mês início"
                  size="sm"
                  class="w-full"
                />
              </UFormField>
              <span class="mb-2 hidden text-muted 2xl:block">até</span>
              <UFormField
                label="Mês fim"
                class="w-full"
              >
                <UInputMenu
                  v-model="filtroMesFim"
                  :items="mesesOpcoes"
                  placeholder="Mês fim"
                  size="sm"
                  class="w-full"
                />
              </UFormField>
            </div>
            <UFormField
              label="Médico"
              class="w-full"
            >
              <UInputMenu
                v-model="filtroMedico"
                :items="medicosDisponiveis"
                placeholder="Médico"
                size="sm"
                class="w-full"
              />
            </UFormField>
            <UFormField
              label="Especialidade"
              class="w-full"
            >
              <UInputMenu
                v-model="filtroEspecialidade"
                :items="especialidadesDisponiveis"
                placeholder="Especialidade"
                size="sm"
                class="w-full"
              />
            </UFormField>
            <UFormField
              label="Convênio"
              class="w-full"
            >
              <UInputMenu
                v-model="filtroConvenio"
                :items="conveniosDisponiveis"
                placeholder="Convênio"
                size="sm"
                class="w-full"
              />
            </UFormField>
            <UFormField
              label="Status"
              class="w-full"
            >
              <UInputMenu
                v-model="filtroStatus"
                :items="statusDisponiveis"
                placeholder="Status"
                size="sm"
                class="w-full"
              />
            </UFormField>
            <UButton
              label="Aplicar Filtros"
              icon="i-lucide-filter"
              size="sm"
              color="primary"
              class="min-h-10 w-full sm:w-auto"
              @click="aplicarFiltros"
            />
          </div>
          <div class="grid grid-cols-1 items-end gap-3 sm:grid-cols-2">
            <UFormField
              label="Exame"
              class="w-full"
            >
              <UInput
                v-model="filtroExame"
                placeholder="Buscar exame..."
                size="sm"
                class="w-full"
              />
            </UFormField>
            <UFormField
              label="Paciente"
              class="w-full"
            >
              <UInput
                v-model="filtroPaciente"
                placeholder="Nome, CPF ou prontuário..."
                size="sm"
                class="w-full"
              />
            </UFormField>
          </div>
        </div>
      </UCard>

      <UAlert
        v-if="errorMsg"
        :title="errorMsg"
        color="error"
        variant="subtle"
        icon="i-lucide-circle-alert"
      />

      <div class="grid w-full grid-cols-1 items-stretch gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <CardRetencao
          class="h-full"
          titulo="Exames Solicitados"
          :valor="totalExamesSolicitados"
          cor="info"
          icone="i-lucide-flask-conical"
        />
        <CardRetencao
          class="h-full"
          titulo="Realizados"
          :valor="totalRealizadosInternamente"
          cor="success"
          icone="i-lucide-check-circle"
        />
        <CardRetencao
          class="h-full"
          titulo="Pendentes"
          :valor="totalPendentes"
          cor="warning"
          icone="i-lucide-clock"
        />
        <CardRetencao
          class="h-full"
          titulo="Não Convertidos"
          :valor="totalNaoConvertidos"
          cor="error"
          icone="i-lucide-x-circle"
        />
        <CardRetencao
          class="h-full"
          titulo="Taxa de Conversão"
          :valor="taxaConversao"
          medida="%"
          cor="primary"
          icone="i-lucide-trending-up"
        />
        <CardRetencao
          class="h-full"
          titulo="Faturamento Realizado"
          :valor="`R$ ${faturamentoRealizado.toLocaleString('pt-BR')}`"
          cor="success"
          icone="i-lucide-coins"
        />
      </div>

      <div class="w-full grid grid-cols-1 lg:grid-cols-2 gap-4">
        <UCard>
          <template #title>
            <p class="text-lg font-medium">
              Conversão por Médico
            </p>
          </template>
          <ChartConversaoMedico
            :medicos="chartConversaoMedicos"
            :taxas="chartConversaoTaxas"
          />
        </UCard>
        <UCard>
          <template #title>
            <p class="text-lg font-medium">
              Exames mais Solicitados
            </p>
          </template>
          <ChartExamesMaisSolicitados
            :labels="chartExamesLabels"
            :dados="chartExamesDados"
          />
        </UCard>
      </div>

      <div class="w-full grid grid-cols-1 lg:grid-cols-2 gap-4">
        <UCard>
          <template #title>
            <p class="text-lg font-medium">
              Oportunidade Financeira por Convênio
            </p>
          </template>
          <ChartOportunidadeFinanceira
            :labels="chartOportunidadeLabels"
            :dados="chartOportunidadeDados"
          />
        </UCard>
        <UCard>
          <template #title>
            <p class="text-lg font-medium">
              Conversão por Especialidade
            </p>
          </template>
          <ChartEspecialidade
            :labels="chartEspecialidadeLabels"
            :dados="chartEspecialidadeDados"
          />
        </UCard>
      </div>

      <div class="grid grid-cols-1 lg:grid-cols-5 gap-4 items-stretch">
        <UCard
          :ui="{
            body: 'p-4 sm:p-4 sm:py-5 min-w-0 flex items-center h-full'
          }"
          class="col-span-1 lg:col-span-2"
        >
          <div class="flex min-w-0 items-center gap-3 w-full">
            <UBadge
              class="aspect-square"
              variant="soft"
              color="info"
            >
              <UIcon
                name="i-lucide-trending-up"
                class="size-8 text-info"
              />
            </UBadge>
            <div class="min-w-0 flex-1">
              <p class="break-words text-sm font-bold">
                Tendência de Solicitações
              </p>
              <p class="text-xs text-muted">
                Período selecionado
              </p>
            </div>
          </div>
        </UCard>
        <UCard
          :ui="{
            body: 'p-5 flex items-center h-full'
          }"
          class="col-span-1 lg:col-span-3"
        >
          <div class="flex flex-col gap-3 items-center justify-between w-full sm:flex-row">
            <div class="flex items-center gap-2">
              <UIcon
                name="i-lucide-download"
                class="text-primary size-5"
              />
              <span class="font-semibold">Exportar Dados</span>
            </div>
            <div class="grid w-full grid-cols-2 gap-2 sm:w-auto">
              <UButton
                icon="i-lucide-file-text"
                label="Exportar PDF"
                color="error"
                size="sm"
                class="min-h-10 justify-center"
              />
              <UButton
                icon="i-lucide-file-spreadsheet"
                label="Exportar Excel"
                color="primary"
                size="sm"
                class="min-h-10 justify-center"
              />
            </div>
          </div>
        </UCard>
      </div>

      <UCard class="w-full">
        <template #title>
          <div class="flex flex-col gap-3 xl:flex-row xl:items-center xl:justify-between">
            <p class="text-lg font-medium">
              Exames para Conversão
            </p>
            <div class="grid grid-cols-1 gap-2 sm:grid-cols-2">
              <UInput
                v-model="filtroExame"
                placeholder="Filtrar por exame..."
                size="sm"
                class="w-full sm:w-56"
              />
              <UInput
                v-model="filtroPaciente"
                placeholder="Filtrar por paciente, CPF ou prontuário..."
                size="sm"
                class="w-full sm:w-72"
              />
            </div>
          </div>
        </template>

        <p
          v-if="loading"
          class="py-4 text-sm text-muted"
        >
          Carregando exames do SPDATA...
        </p>

        <p
          v-else-if="!pacientesVisiveis.length"
          class="py-4 text-sm text-muted"
        >
          Nenhum exame encontrado para conversão.
        </p>

        <div
          v-else
          class="flex flex-col gap-2"
        >
          <UPageCard
            v-for="item in pacientesPaginados"
            :key="item.id"
            variant="ghost"
            class="border-b border-muted rounded-none"
            :ui="{ container: 'px-4 sm:p-1 pb-3 sm:px-4' }"
          >
            <div class="grid min-w-0 grid-cols-1 gap-x-4 gap-y-3 sm:grid-cols-2 lg:grid-cols-4 xl:grid-cols-[minmax(0,1.7fr)_minmax(0,1.3fr)_minmax(6.5rem,0.7fr)_minmax(0,1.5fr)_4rem_7rem_7rem] xl:items-center">
              <div class="min-w-0 sm:col-span-2 lg:col-span-2 xl:col-span-1">
                <p class="text-sm text-muted font-bold">
                  Paciente
                </p>
                <div class="flex min-w-0 items-center gap-3">
                  <UAvatar
                    :alt="item.paciente"
                    color="primary"
                    size="sm"
                  />
                  <div class="min-w-0">
                    <p class="wrap-break-word font-medium">
                      {{ item.paciente }}
                    </p>
                    <p class="wrap-break-word text-xs text-muted">
                      {{ item.convenio }}
                    </p>
                  </div>
                </div>
              </div>

              <div class="min-w-0">
                <p class="text-sm text-muted font-bold">
                  Médico
                </p>
                <div class="min-w-0 text-sm">
                  <p class="wrap-break-word font-medium">
                    {{ item.medico }}
                  </p>
                  <p class="wrap-break-word text-xs text-muted">
                    {{ item.crm }}
                  </p>
                </div>
              </div>

              <div class="min-w-0">
                <p class="text-sm text-muted font-bold">
                  Data Solic.
                </p>
                <p class="text-sm">
                  {{ formatarData(item.dataSolicitacao) }}
                </p>
              </div>

              <div class="min-w-0 sm:col-span-2 lg:col-span-2 xl:col-span-1">
                <p class="text-sm text-muted font-bold">
                  Exame
                </p>
                <div class="min-w-0 text-sm">
                  <UTooltip :text="item.exame">
                    <p class="wrap-break-word cursor-default text-sm font-medium">
                      {{ item.exame }}
                    </p>
                  </UTooltip>
                  <p class="wrap-break-word text-xs text-muted">
                    {{ item.codigoTuss }}
                  </p>
                </div>
              </div>

              <div class="min-w-0">
                <p class="text-sm text-muted font-bold">
                  Dias
                </p>
                <UBadge
                  :label="String(item.diasEmAberto)"
                  :color="item.diasEmAberto > 60 ? 'error' : item.diasEmAberto > 30 ? 'warning' : 'neutral'"
                  variant="soft"
                  size="sm"
                />
              </div>

              <div class="min-w-0">
                <p class="text-sm text-muted font-bold">
                  Status
                </p>
                <UBadge
                  :label="rotuloStatus(item.status)"
                  :color="corStatus(item.status)"
                  variant="subtle"
                />
              </div>

              <div class="min-w-0">
                <p class="text-sm text-muted font-bold">
                  Valor Est.
                </p>
                <p class="text-sm font-medium">
                  {{ formatarMoeda(item.valorEstimado) }}
                </p>
              </div>
            </div>
          </UPageCard>
        </div>

        <div
          v-if="pacientesVisiveis.length && !loading"
          class="flex justify-center pt-4"
        >
          <UPagination
            :page="page"
            :items-per-page="pageSize"
            :total="pacientesVisiveis.length"
            :sibling-count="1"
            :ui="{ list: 'flex flex-wrap items-center gap-1 justify-center' }"
            @update:page="page = $event"
          />
        </div>
      </UCard>
    </div>

    <USlideover v-model:open="slideoverAberto">
      <template #header>
        <div class="flex min-w-0 items-center gap-3">
          <UAvatar
            :alt="pacienteSelecionado?.paciente"
            color="primary"
            size="md"
          />
          <div class="min-w-0">
            <p class="break-words font-semibold text-lg">
              {{ pacienteSelecionado?.paciente }}
            </p>
            <p class="break-all text-sm text-muted">
              {{ pacienteSelecionado?.convenio }} | {{ pacienteSelecionado?.cpf }}
            </p>
          </div>
        </div>
      </template>

      <template #body>
        <div class="space-y-6">
          <UCard>
            <template #title>
              <p class="font-semibold">
                Dados do Paciente
              </p>
            </template>
            <div class="grid grid-cols-1 gap-4 text-sm sm:grid-cols-2">
              <div>
                <p class="text-muted">
                  Nome
                </p>
                <p class="break-words font-medium">
                  {{ pacienteSelecionado?.paciente }}
                </p>
              </div>
              <div>
                <p class="text-muted">
                  CPF
                </p>
                <p class="font-medium">
                  {{ pacienteSelecionado?.cpf }}
                </p>
              </div>
              <div>
                <p class="text-muted">
                  Prontuário
                </p>
                <p class="font-medium">
                  {{ pacienteSelecionado?.prontuario }}
                </p>
              </div>
              <div>
                <p class="text-muted">
                  Telefone
                </p>
                <p class="font-medium">
                  {{ pacienteSelecionado?.telefone }}
                </p>
              </div>
              <div>
                <p class="text-muted">
                  Convênio
                </p>
                <p class="font-medium">
                  {{ pacienteSelecionado?.convenio }}
                </p>
              </div>
            </div>
          </UCard>

          <UCard>
            <template #title>
              <p class="font-semibold">
                Dados da Solicitação
              </p>
            </template>
            <div class="grid grid-cols-1 gap-4 text-sm sm:grid-cols-2">
              <div>
                <p class="text-muted">
                  Médico
                </p>
                <p class="font-medium">
                  {{ pacienteSelecionado?.medico }}
                </p>
              </div>
              <div>
                <p class="text-muted">
                  CRM
                </p>
                <p class="font-medium">
                  {{ pacienteSelecionado?.crm }}
                </p>
              </div>
              <div>
                <p class="text-muted">
                  Especialidade
                </p>
                <p class="font-medium">
                  {{ pacienteSelecionado?.especialidade }}
                </p>
              </div>
              <div>
                <p class="text-muted">
                  Data da Solicitação
                </p>
                <p class="font-medium">
                  {{ pacienteSelecionado ? formatarData(pacienteSelecionado.dataSolicitacao) : '' }}
                </p>
              </div>
              <div>
                <p class="text-muted">
                  Dias em Aberto
                </p>
                <p class="font-medium">
                  {{ pacienteSelecionado?.diasEmAberto }} dias
                </p>
              </div>
              <div>
                <p class="text-muted">
                  Status
                </p>
                <UBadge
                  v-if="pacienteSelecionado"
                  :label="rotuloStatus(pacienteSelecionado.status)"
                  :color="corStatus(pacienteSelecionado.status)"
                  variant="subtle"
                />
              </div>
            </div>
          </UCard>

          <UCard>
            <template #title>
              <p class="font-semibold">
                Exames Solicitados
              </p>
            </template>
            <div class="max-w-full overflow-x-auto">
              <table class="min-w-[36rem] w-full text-sm">
                <thead>
                  <tr class="border-b border-neutral-200 dark:border-neutral-800">
                    <th class="text-left py-2 font-medium text-muted">
                      Exame
                    </th>
                    <th class="text-left py-2 font-medium text-muted">
                      TUSS
                    </th>
                    <th class="text-right py-2 font-medium text-muted">
                      Valor Est.
                    </th>
                    <th class="text-left py-2 font-medium text-muted">
                      Status
                    </th>
                  </tr>
                </thead>
                <tbody>
                  <tr
                    v-for="exame in examesPacienteSelecionado"
                    :key="exame.id"
                    class="border-t border-neutral-200 dark:border-neutral-800"
                  >
                    <td class="py-2">
                      {{ exame.exame }}
                    </td>
                    <td class="py-2">
                      {{ exame.codigoTuss }}
                    </td>
                    <td class="py-2 text-right">
                      {{ formatarMoeda(exame.valorEstimado) }}
                    </td>
                    <td class="py-2">
                      <UBadge
                        :label="rotuloStatus(exame.status)"
                        :color="corStatus(exame.status)"
                        variant="subtle"
                        size="sm"
                      />
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </UCard>

          <UCard>
            <template #title>
              <p class="font-semibold">
                Histórico de Contato
              </p>
            </template>
            <div class="space-y-4">
              <p
                v-if="!historicoContato.length"
                class="text-sm text-muted"
              >
                Nenhum histórico de contato registrado para este exame.
              </p>

              <div
                v-for="(contato, idx) in historicoContato"
                :key="idx"
                class="flex gap-3 pb-4 border-b border-neutral-200 dark:border-neutral-800 last:border-0"
              >
                <div class="flex flex-col items-center">
                  <div class="size-2 rounded-full bg-primary mt-2" />
                  <div
                    v-if="idx < historicoContato.length - 1"
                    class="w-px flex-1 bg-neutral-200 dark:bg-neutral-800"
                  />
                </div>
                <div class="flex-1">
                  <div class="flex flex-col gap-1 sm:flex-row sm:items-center sm:justify-between">
                    <p class="text-sm font-medium">
                      {{ contato.canal }}
                    </p>
                    <p class="text-xs text-muted">
                      {{ contato.data }}
                    </p>
                  </div>
                  <p class="text-sm text-muted">
                    {{ contato.usuario }} - {{ contato.resultado }}
                  </p>
                  <p
                    v-if="contato.observacao"
                    class="text-xs text-muted mt-1"
                  >
                    {{ contato.observacao }}
                  </p>
                </div>
              </div>
            </div>
          </UCard>

          <UCard>
            <template #title>
              <p class="font-semibold">
                Ações Rápidas
              </p>
            </template>
            <div class="grid grid-cols-1 gap-2 sm:flex sm:flex-wrap">
              <UButton
                icon="i-lucide-message-circle"
                label="WhatsApp"
                color="success"
                size="sm"
                class="min-h-10 justify-center"
                @click="pacienteSelecionado ? whatsapp(pacienteSelecionado) : undefined"
              />
              <UButton
                icon="i-lucide-phone"
                label="Ligar"
                color="primary"
                size="sm"
                class="min-h-10 justify-center"
                @click="pacienteSelecionado ? ligar(pacienteSelecionado) : undefined"
              />
              <UButton
                icon="i-lucide-calendar-plus"
                label="Agendar"
                color="warning"
                size="sm"
                class="min-h-10 justify-center"
                @click="pacienteSelecionado ? agendar(pacienteSelecionado) : undefined"
              />
              <UDropdownMenu :items="itensAcoes">
                <UButton
                  icon="i-lucide-chevron-down"
                  label="Atualizar Status"
                  color="secondary"
                  size="sm"
                  class="min-h-10 w-full justify-center sm:w-auto"
                />
              </UDropdownMenu>
            </div>
          </UCard>
        </div>
      </template>
    </USlideover>
  </div>
</template>
