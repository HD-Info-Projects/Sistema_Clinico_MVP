<script setup lang="ts">
import type { DropdownMenuItem } from '@nuxt/ui/'

const openNav = inject<() => void>('openNav', () => {})
const auth = useAuthStore()

const userName = computed(() => auth.user?.nome || 'Usuário')

const motivosNoShow = [
  { value: 'esquecimento', label: 'Esquecimento', description: 'Paciente esqueceu a consulta.', icon: 'i-lucide-brain' },
  { value: 'transporte', label: 'Transporte', description: 'Paciente teve dificuldade de deslocamento.', icon: 'i-lucide-bus' },
  { value: 'outros', label: 'Outros', description: 'Motivo não classificado nas opções anteriores.', icon: 'i-lucide-message-square' }
] as const

type MotivoNoShow = typeof motivosNoShow[number]['value']

interface PacienteNoShow {
  id: number
  spdataAgendaId: number
  medsystemAtendimentoId: number | null
  nome: string
  telefone: string
  convenio: string
  medico: string
  especialidade: string
  dataFalta: string
  horario: string
  status: 'nao-confirmado' | 'faltou'
  situacao: string
  motivo: 'esquecimento' | 'transporte' | 'outros' | null
  recuperado: boolean
  cpf: string
  prontuario: string
}

interface NoShowResponse {
  items: PacienteNoShow[]
  total: number
  page: number
  pageSize: number
  resumo: {
    totalResgate: number
    faltou: number
    naoConfirmado: number
    recuperados: number
    semContato: number
  }
  filtros: {
    medicos: string[]
    especialidades: string[]
    convenios: string[]
    anos: string[]
  }
  graficos: {
    porMes: Array<{ label: string, total: number }>
    porEspecialidade: Array<{ label: string, total: number }>
    porDiaSemana: Array<{ label: string, total: number }>
  }
}

type NoShowResumo = NoShowResponse['resumo']
type NoShowGraficos = NoShowResponse['graficos']

const pacientesNoShow = ref<PacienteNoShow[]>([])
const loading = ref(false)
const modalRecusouAberto = ref(false)
const pacienteRecusouSelecionado = ref<PacienteNoShow | null>(null)
const errorMsg = ref('')
const motivoErrorMsg = ref('')
const motivoModalAberto = ref(false)
const pacienteMotivo = ref<PacienteNoShow | null>(null)
const motivoSelecionado = ref<MotivoNoShow | undefined>()
const salvandoMotivo = ref(false)
const totalNoShow = ref(0)
const resumoNoShow = ref<NoShowResumo>({
  totalResgate: 0,
  faltou: 0,
  naoConfirmado: 0,
  recuperados: 0,
  semContato: 0
})
const graficosNoShow = ref<NoShowGraficos>({
  porMes: [],
  porEspecialidade: [],
  porDiaSemana: []
})

const filtrosDisponiveis = ref<NoShowResponse['filtros']>({
  medicos: [],
  especialidades: [],
  convenios: [],
  anos: []
})

const motivosNoShowItems = computed(() => motivosNoShow.map(item => ({ ...item })))

const hoje = new Date()
const anoAtual = String(hoje.getFullYear())
const mesesOpcoes = ['Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho', 'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro']
const mesAtualNome = mesesOpcoes[hoje.getMonth()] || 'Janeiro'

const MES_PARA_NUMERO: Record<string, string> = {
  Janeiro: '01', Fevereiro: '02', Março: '03', Abril: '04',
  Maio: '05', Junho: '06', Julho: '07', Agosto: '08',
  Setembro: '09', Outubro: '10', Novembro: '11', Dezembro: '12'
}

const filtro = ref('')
const filtroAno = ref(anoAtual)
const filtroMesInicio = ref(mesAtualNome)
const filtroMesFim = ref(mesAtualNome)
const filtroMedico = ref('Todos')
const filtroEspecialidade = ref('Todos')
const filtroConvenio = ref('Todos')

const filtroAnoActive = ref(anoAtual)
const filtroMesInicioActive = ref(mesAtualNome)
const filtroMesFimActive = ref(mesAtualNome)
const filtroMedicoActive = ref('Todos')
const filtroEspecialidadeActive = ref('Todos')
const filtroConvenioActive = ref('Todos')

const filtroPeriodoInicioActive = computed(() => `${filtroAnoActive.value}-${MES_PARA_NUMERO[filtroMesInicioActive.value]}`)
const filtroPeriodoFimActive = computed(() => `${filtroAnoActive.value}-${MES_PARA_NUMERO[filtroMesFimActive.value]}`)

function aplicarFiltros() {
  filtroAnoActive.value = filtroAno.value
  filtroMesInicioActive.value = filtroMesInicio.value
  filtroMesFimActive.value = filtroMesFim.value
  filtroMedicoActive.value = filtroMedico.value
  filtroEspecialidadeActive.value = filtroEspecialidade.value
  filtroConvenioActive.value = filtroConvenio.value
  page.value = 1
  carregarNoShow()
}

function ultimoDiaMes(ano: string, mes: string) {
  return new Date(Number(ano), Number(MES_PARA_NUMERO[mes] || '01'), 0).getDate()
}

function dataInicioFiltro() {
  return `${filtroAno.value}-${MES_PARA_NUMERO[filtroMesInicio.value] || '01'}-01`
}

function dataFimFiltro() {
  const mes = MES_PARA_NUMERO[filtroMesFim.value] || '01'
  return `${filtroAno.value}-${mes}-${String(ultimoDiaMes(filtroAno.value, filtroMesFim.value)).padStart(2, '0')}`
}

function limparDadosNoShow() {
  pacientesNoShow.value = []
  totalNoShow.value = 0
  resumoNoShow.value = {
    totalResgate: 0,
    faltou: 0,
    naoConfirmado: 0,
    recuperados: 0,
    semContato: 0
  }
  graficosNoShow.value = {
    porMes: [],
    porEspecialidade: [],
    porDiaSemana: []
  }
}

async function carregarNoShow() {
  const unidadeId = auth.activeClinicaId
  loading.value = true
  errorMsg.value = ''

  if (!unidadeId) {
    limparDadosNoShow()
    errorMsg.value = 'Selecione uma unidade para carregar no-show'
    loading.value = false
    return
  }

  const params = new URLSearchParams()
  params.set('dataIni', dataInicioFiltro())
  params.set('dataFim', dataFimFiltro())
  params.set('page', '1')
  params.set('pageSize', '500')
  params.set('unidadeId', String(unidadeId))

  if (filtroMedico.value !== 'Todos') params.set('medico', filtroMedico.value)
  if (filtroEspecialidade.value !== 'Todos') params.set('especialidade', filtroEspecialidade.value)
  if (filtroConvenio.value !== 'Todos') params.set('convenio', filtroConvenio.value)

  try {
    const response = await $fetch<NoShowResponse>(`/api/no-show?${params.toString()}`)
    pacientesNoShow.value = response.items
    totalNoShow.value = response.total
    resumoNoShow.value = response.resumo
    graficosNoShow.value = response.graficos
    filtrosDisponiveis.value = response.filtros
  } catch {
    limparDadosNoShow()
    errorMsg.value = 'Erro ao carregar lista de resgate'
  } finally {
    loading.value = false
  }
}

const anosDisponiveis = computed(() => {
  const anos = [...new Set([...filtrosDisponiveis.value.anos, anoAtual])].sort()
  return anos.length ? anos : [anoAtual]
})

function opcaoFiltro(valor: string | null | undefined) {
  const texto = String(valor ?? '').trim()
  if (!texto || texto === '0' || texto.toLowerCase() === 'não informado') return ''
  return texto
}

function montarOpcoesFiltro(opcoes: string[]) {
  const itens = [...new Set(opcoes.map(opcaoFiltro).filter(Boolean))]
  return ['Todos', ...itens.sort((a, b) => a.localeCompare(b, 'pt-BR'))]
}

const medicosOptions = computed(() => {
  const all = filtrosDisponiveis.value.medicos.length
    ? filtrosDisponiveis.value.medicos
    : pacientesNoShow.value.map(p => p.medico)
  return montarOpcoesFiltro(all)
})

const conveniosOptions = computed(() => {
  const all = filtrosDisponiveis.value.convenios.length
    ? filtrosDisponiveis.value.convenios
    : pacientesNoShow.value.map(p => p.convenio)
  return montarOpcoesFiltro(all)
})

const especialidadesOptions = computed(() => {
  const all = filtrosDisponiveis.value.especialidades.length
    ? filtrosDisponiveis.value.especialidades
    : pacientesNoShow.value.map(p => p.especialidade)
  return montarOpcoesFiltro(all)
})

const dadosFiltrados = computed(() => {
  return pacientesNoShow.value.filter((p) => {
    if (filtroMedicoActive.value !== 'Todos' && opcaoFiltro(p.medico) !== filtroMedicoActive.value) return false
    if (filtroEspecialidadeActive.value !== 'Todos' && opcaoFiltro(p.especialidade) !== filtroEspecialidadeActive.value) return false
    if (filtroConvenioActive.value !== 'Todos' && opcaoFiltro(p.convenio) !== filtroConvenioActive.value) return false
    if (p.dataFalta.substring(0, 7) < filtroPeriodoInicioActive.value) return false
    if (p.dataFalta.substring(0, 7) > filtroPeriodoFimActive.value) return false
    return true
  })
})

const MESES_LABELS = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']

const chartMeses = computed(() => {
  const inicio = parseInt(MES_PARA_NUMERO[filtroMesInicioActive.value]!) - 1
  const fim = parseInt(MES_PARA_NUMERO[filtroMesFimActive.value]!)
  return MESES_LABELS.slice(inicio, fim)
})

const chartDados = computed(() => {
  const inicio = parseInt(MES_PARA_NUMERO[filtroMesInicioActive.value]!) - 1
  const fim = parseInt(MES_PARA_NUMERO[filtroMesFimActive.value]!)
  const totaisPorMes = new Map(graficosNoShow.value.porMes.map(item => [item.label, item.total] as const))

  return MESES_LABELS.slice(inicio, fim).map((_, index) => {
    const mes = String(inicio + index + 1).padStart(2, '0')
    return totaisPorMes.get(`${filtroAnoActive.value}-${mes}`) || 0
  })
})

const DIAS_LABELS = ['Dom', 'Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb']

const chartEspecialidade = computed(() => {
  return {
    labels: graficosNoShow.value.porEspecialidade.map(item => item.label),
    dados: graficosNoShow.value.porEspecialidade.map(item => item.total)
  }
})

const chartDiaSemana = computed(() => {
  const totaisPorDia = new Map(graficosNoShow.value.porDiaSemana.map(item => [item.label, item.total] as const))
  return {
    labels: DIAS_LABELS,
    dados: DIAS_LABELS.map(label => totaisPorDia.get(label) || 0)
  }
})

const totalFiltrado = computed(() => resumoNoShow.value.totalResgate || totalNoShow.value)
const totalFaltou = computed(() => resumoNoShow.value.faltou)
const totalNaoConfirmado = computed(() => resumoNoShow.value.naoConfirmado)
const totalSemContato = computed(() => resumoNoShow.value.semContato)
const totalNaoInformado = computed(() => dadosFiltrados.value.filter(p => !p.motivo).length)
const motivosGrafico = computed(() => [
  ...motivosNoShow.map(motivo => ({
    label: motivo.label,
    total: dadosFiltrados.value.filter(p => p.motivo === motivo.value).length
  })),
  { label: 'Não informado', total: totalNaoInformado.value }
])

const agendamentosRecuperados = computed(() => resumoNoShow.value.recuperados)

const taxaRecuperacao = computed(() => {
  const total = totalFiltrado.value
  return total > 0 ? Math.round((agendamentosRecuperados.value / total) * 100) : 0
})

const pacientesVisiveis = computed(() => {
  let lista = dadosFiltrados.value
  const termo = filtro.value.toLowerCase().trim()
  if (termo) {
    lista = lista.filter(p => p.nome.toLowerCase().includes(termo) || p.telefone.includes(termo))
  }
  return lista
})

const page = ref(1)
const pageSize = 7

const pacientesPaginados = computed(() => {
  const inicio = (page.value - 1) * pageSize
  return pacientesVisiveis.value.slice(inicio, inicio + pageSize)
})

function corStatus(status: string) {
  switch (status) {
    case 'nao-confirmado': return 'quinary'
    case 'faltou': return 'error'
    default: return 'neutral'
  }
}

function rotuloStatus(status: string) {
  switch (status) {
    case 'nao-confirmado': return 'Desistente'
    case 'faltou': return 'Faltou'
    default: return status
  }
}

function rotuloMotivo(motivo: PacienteNoShow['motivo']) {
  if (!motivo) return 'Não informado'
  return motivosNoShow.find(item => item.value === motivo)?.label ?? motivo
}

function formatarData(iso: string) {
  const [ano, mes, dia] = iso.split('-')
  return `${dia}/${mes}/${ano}`
}

function ligar(paciente: PacienteNoShow) {
  const tel = paciente.telefone.replace(/\D/g, '')
  if (!tel) return
  window.location.href = `tel:${tel}`
}

function reagendar(paciente: PacienteNoShow) {
  void paciente
}

function recusou(paciente: PacienteNoShow) {
  pacientesNoShow.value = pacientesNoShow.value.filter(p => p.id !== paciente.id)
}

function abrirModalMotivo(paciente: PacienteNoShow) {
  pacienteMotivo.value = paciente
  motivoSelecionado.value = paciente.motivo ?? undefined
  motivoErrorMsg.value = ''
  motivoModalAberto.value = true
}

function itensMais(paciente: PacienteNoShow): DropdownMenuItem[][] {
  return [
    [
      {
        label: 'Registrar Motivo da Falta',
        icon: 'i-lucide-message-square',
        onSelect: () => abrirModalMotivo(paciente)
      }
    ],
    [
      {
        label: 'Bloquear Agendamento Futuro',
        icon: 'i-lucide-ban'
      }
    ],
    [
      {
        label: 'Impacto Financeiro',
        icon: 'i-lucide-dollar-sign'
      },
      {
        label: 'Indicadores do Paciente',
        icon: 'i-lucide-bar-chart-3'
      }
    ]
  ]
}

async function salvarMotivoFalta() {
  if (!pacienteMotivo.value || !motivoSelecionado.value) return

  const unidadeId = auth.activeClinicaId
  if (!unidadeId) {
    motivoErrorMsg.value = 'Selecione uma unidade para registrar o motivo da falta'
    return
  }

  salvandoMotivo.value = true
  motivoErrorMsg.value = ''

  const params = new URLSearchParams()
  params.set('unidadeId', String(unidadeId))

  try {
    const response = await $fetch<{ id: number, motivo: MotivoNoShow }>(`/api/no-show/${pacienteMotivo.value.id}/motivo?${params.toString()}`, {
      method: 'PATCH',
      body: { motivo: motivoSelecionado.value }
    })

    const idx = pacientesNoShow.value.findIndex(p => p.id === response.id)
    if (idx >= 0) {
      pacientesNoShow.value[idx] = { ...pacientesNoShow.value[idx]!, motivo: response.motivo }
      pacienteMotivo.value = pacientesNoShow.value[idx]!
    }

    motivoModalAberto.value = false
  } catch {
    motivoErrorMsg.value = 'Erro ao registrar motivo da falta'
  } finally {
    salvandoMotivo.value = false
  }
}

onMounted(() => {
  carregarNoShow()
})

watch(() => auth.activeClinicaId, () => {
  carregarNoShow()
})
</script>

<template>
  <div>
    <UHeader
      title="No-show"
      toggle-side="left"
    >
      <template #toggle>
        <UButton
          icon="i-lucide-menu"
          color="neutral"
          variant="ghost"
          class="lg:hidden"
          aria-label="Abrir menu"
          @click="openNav()"
        />
      </template>
      <template #right>
        <div class="flex items-center gap-2">
          <UBadge
            :label="userName"
            color="neutral"
            variant="soft"
            class="hidden lg:inline-flex"
          />
          <UColorModeButton />
        </div>
      </template>
    </UHeader>
    <div class="min-h-screen min-w-0 space-y-6 bg-neutral-100 p-3 dark:bg-neutral-950 sm:space-y-8 sm:p-6">
      <div class="w-full gap-4">
        <UCard class="w-full">
          <template #title>
            <p class="text-lg font-medium">
              Filtros de Análise
            </p>
          </template>
          <div class="space-y-4">
            <div class="grid grid-cols-1 items-end gap-3 sm:grid-cols-2 xl:grid-cols-4 2xl:grid-cols-7">
              <div class="grid grid-cols-2 items-end gap-2 sm:col-span-2 xl:col-span-2 2xl:col-span-3 2xl:grid-cols-[6rem_1fr_auto_1fr]">
                <UFormField
                  label="Ano"
                  class="w-full"
                >
                  <UInputMenu
                    v-model="filtroAno"
                    :items="anosDisponiveis"
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
                  :items="medicosOptions"
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
                  :items="especialidadesOptions"
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
                  :items="conveniosOptions"
                  placeholder="Convênio"
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
          </div>
        </UCard>
      </div>

      <UAlert
        v-if="errorMsg"
        :title="errorMsg"
        color="error"
        variant="subtle"
        icon="i-lucide-circle-alert"
      />

      <div class="w-full grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 items-center gap-4">
        <CardInformativo
          titulo="Taxa de Recuperação"
          :valor="taxaRecuperacao"
          medida="%"
          cor="primary"
          icone="i-lucide-trending-up"
        />
        <CardInformativo
          titulo="Desistentes"
          :valor="totalNaoConfirmado"
          cor="quinary"
          icone="lucide:user-round-x"
        />
        <CardInformativo
          titulo="Faltou"
          :valor="totalFaltou"
          cor="error"
          icone="i-lucide-calendar-x"
        />
        <CardInformativo
          titulo="Sem contato"
          :valor="totalSemContato"
          cor="secondary"
          icone="i-lucide-clock"
        />
        <CardInformativo
          titulo="Lista de resgate"
          :valor="totalFiltrado"
          cor="tertiary"
          icone="lucide:user-round-search"
        />
      </div>
      <div class="w-full grid grid-cols-1 lg:grid-cols-3 gap-4">
        <UCard class="col-span-1">
          <template #title>
            <p class="text-lg font-medium">
              Motivos de Falta
            </p>
          </template>
          <ChartMotivosFaltas
            :total="totalFiltrado"
            :items="motivosGrafico"
          />
        </UCard>
        <UCard class="col-span-1 lg:col-span-2">
          <template #title>
            <p class="text-lg font-medium">
              Tendência de No-Show
            </p>
          </template>

          <ChartTendencia
            :labels="chartMeses"
            :dados="chartDados"
          />
        </UCard>
      </div>
      <div class="w-full grid grid-cols-1 lg:grid-cols-3 gap-4">
        <UCard class="col-span-1 lg:col-span-2">
          <template #title>
            <p class="text-lg font-medium">
              Taxa de no show por dia da semana
            </p>
          </template>

          <ChartDiaSemana
            :labels="chartDiaSemana.labels"
            :dados="chartDiaSemana.dados"
          />
        </UCard>
        <UCard class="col-span-1">
          <template #title>
            <p class="text-lg font-medium">
              Taxa de no show por especialidade
            </p>
          </template>
          <ChartEspecialidade
            :labels="chartEspecialidade.labels"
            :dados="chartEspecialidade.dados"
          />
        </UCard>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-5 gap-4 items-stretch">
        <UCard
          :ui="{
            body: 'p-4 sm:p-4 sm:py-5 min-w-0 flex items-center h-full'
          }"
          class="md:col-span-2"
        >
          <div class="flex min-w-0 flex-wrap items-center gap-3 w-full">
            <UBadge
              class="aspect-square"
              variant="soft"
              color="error"
            >
              <UIcon
                name="lucide:coins"
                :class="`size-8 text-primary bg-error`"
              />
            </UBadge>
            <div class="min-w-0 flex-1">
              <p class="break-words text-sm font-bold">
                Impacto Financeiro (estimado)
              </p>
              <p :class="`text-2xl font-black text-error`">
                R$0,00
              </p>
            </div>
            <UBadge
              color="neutral"
              variant="soft"
            >
              Sem regra financeira cadastrada
            </UBadge>
          </div>
        </UCard>
        <UCard
          :ui="{
            body: 'p-5 flex items-center h-full'
          }"
          class="md:col-span-3"
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
                label="Exportar CSV"
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
          <div class="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
            <p class="text-lg font-medium">
              Resgate de pacientes
            </p>
            <UInput
              v-model="filtro"
              placeholder="Filtrar por paciente ou telefone..."
              size="sm"
              class="w-full sm:w-72"
            />
          </div>
        </template>

        <p
          v-if="loading"
          class="py-4 text-sm text-muted"
        >
          Carregando lista de resgate...
        </p>

        <p
          v-else-if="!pacientesVisiveis.length"
          class="py-4 text-sm text-muted"
        >
          Nenhum paciente encontrado para resgate.
        </p>

        <div
          v-else
          class="flex flex-col gap-2"
        >
          <UPageCard
            v-for="item in pacientesPaginados"
            :key="item.id"
            :ui="{ container: 'p-1 sm:p-1' }"
          >
            <div class="grid min-w-0 grid-cols-1 gap-x-4 gap-y-3 sm:grid-cols-2 md:grid-cols-8 md:items-center">
              <div class="col-span-2">
                <p class="text-sm text-muted font-bold text-center sm:text-left">
                  Paciente
                </p>
                <div class="flex min-w-0 items-center justify-center gap-3 sm:justify-start">
                  <UAvatar
                    :alt="item.nome"
                    color="primary"
                    size="sm"
                  />
                  <div class="min-w-0">
                    <p class="break-words font-medium">
                      {{ item.nome }}
                    </p>
                    <p class="text-xs text-muted">
                      {{ item.convenio || 'Convênio não informado' }}
                    </p>
                  </div>
                </div>
              </div>

              <div class="md:col-span-1 text-center">
                <p class="text-sm text-muted font-bold">
                  Telefone
                </p>
                <p class="text-sm">
                  {{ item.telefone || 'Não informado' }}
                </p>
              </div>

              <div class="md:col-span-1 text-center">
                <p class="text-sm text-muted font-bold">
                  Data da Falta
                </p>
                <p class="text-sm">
                  {{ formatarData(item.dataFalta) }} {{ item.horario || '' }}
                </p>
              </div>

              <div class="md:col-span-1 text-center">
                <p class="text-sm text-muted font-bold">
                  Motivo
                </p>
                <UBadge
                  :label="rotuloMotivo(item.motivo)"
                  :color="item.motivo ? 'info' : 'neutral'"
                  variant="soft"
                />
              </div>

              <div class="md:col-span-1 text-center">
                <p class="text-sm text-muted font-bold">
                  Status
                </p>
                <UBadge
                  :label="rotuloStatus(item.status)"
                  :color="corStatus(item.status)"
                  variant="subtle"
                />
              </div>

              <div class="col-span-2 md:col-span-2 text-center">
                <p class="text-sm text-muted font-bold">
                  Ações
                </p>
                <div class="grid grid-cols-2 justify-center gap-2 sm:flex sm:flex-wrap sm:gap-1">
                  <UButton
                    icon="i-lucide-phone"
                    label="Ligar"
                    size="sm"
                    color="primary"
                    class="min-h-10"
                    @click="ligar(item)"
                  />
                  <UButton
                    icon="i-lucide-calendar-plus"
                    label="Reagendar"
                    size="sm"
                    color="warning"
                    class="min-h-10"
                    @click="reagendar(item)"
                  />
                  <UButton
                    icon="i-lucide-x-circle"
                    label="Recusou"
                    size="sm"
                    color="error"
                    class="min-h-10"
                    @click="pacienteRecusouSelecionado = item; modalRecusouAberto = true"
                  />
                  <UDropdownMenu :items="itensMais(item)">
                    <UButton
                      icon="lucide:menu"
                      label="Mais"
                      size="sm"
                      color="secondary"
                      class="min-h-10"
                    />
                  </UDropdownMenu>
                </div>
              </div>
            </div>
          </UPageCard>
        </div>

        <div
          v-if="!loading && pacientesVisiveis.length"
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

      <ModalConfirmacao
        :abrir="modalRecusouAberto"
        titulo="Marcar como Recusado?"
        descricao="Tem certeza que deseja marcar que esse paciente recusou?"
        texto-confirma="Confirmar"
        cor-confirma="error"
        @fechar="modalRecusouAberto = false; pacienteRecusouSelecionado = null"
        @confirmar="recusou(pacienteRecusouSelecionado!); modalRecusouAberto = false; pacienteRecusouSelecionado = null"
      />
    </div>

    <UModal v-model:open="motivoModalAberto">
      <template #header>
        <div>
          <h2 class="text-lg font-semibold">
            Registrar Motivo da Falta
          </h2>
          <p class="text-sm text-muted mt-0.5">
            {{ pacienteMotivo?.nome || 'Paciente não selecionado' }}
          </p>
        </div>
      </template>

      <template #body>
        <div class="space-y-4">
          <UAlert
            v-if="motivoErrorMsg"
            :title="motivoErrorMsg"
            color="error"
            variant="subtle"
            icon="i-lucide-circle-alert"
          />

          <UFormField
            label="Motivo da falta"
            description="Selecione uma opção cadastrada para classificar o no-show."
          >
            <USelectMenu
              v-model="motivoSelecionado"
              :items="motivosNoShowItems"
              value-key="value"
              label-key="label"
              description-key="description"
              placeholder="Selecione o motivo"
              :search-input="{ placeholder: 'Buscar motivo...' }"
              class="w-full"
            />
          </UFormField>
        </div>
      </template>

      <template #footer>
        <div class="flex justify-end gap-2 w-full">
          <UButton
            label="Cancelar"
            color="neutral"
            variant="ghost"
            :disabled="salvandoMotivo"
            @click="void (motivoModalAberto = false)"
          />
          <UButton
            label="Salvar Motivo"
            icon="i-lucide-save"
            :loading="salvandoMotivo"
            :disabled="!pacienteMotivo || !motivoSelecionado"
            @click="salvarMotivoFalta"
          />
        </div>
      </template>
    </UModal>
  </div>
</template>
