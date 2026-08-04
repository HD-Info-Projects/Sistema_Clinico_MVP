<script setup lang="ts">
import type { DropdownMenuItem } from '@nuxt/ui/'
import { getPaginationRowModel } from '@tanstack/vue-table'

const auth = useAuthStore()

const userName = computed(() => auth.user?.nome || 'Usuário')

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

const itensMais = ref<DropdownMenuItem[][]>([
  /* Grupo: Histórico e Ficha
  [
    {
      label: 'Histórico do Paciente',
      icon: 'i-lucide-clock'
    },
    {
      label: 'Ficha do Paciente',
      icon: 'i-lucide-file-text'
    }
  ],
  */

  // Grupo: Ações da Consulta
  [
    {
      label: 'Registrar Motivo da Falta',
      icon: 'i-lucide-message-square'
    }
  ],

  // Grupo: Classificação e Bloqueio
  [
    {
      label: 'Bloquear Agendamento Futuro',
      icon: 'i-lucide-ban'
    }
  ],

  // Grupo: Indicadores
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
])

const pacientesNoShow = ref<PacienteNoShow[]>([])
const loading = ref(false)
const modalRecusouAberto = ref(false)
const pacienteRecusouSelecionado = ref<PacienteNoShow | null>(null)
const errorMsg = ref('')
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
  pagination.value.pageIndex = 0
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

async function carregarNoShow() {
  loading.value = true
  errorMsg.value = ''

  const params = new URLSearchParams()
  params.set('dataIni', dataInicioFiltro())
  params.set('dataFim', dataFimFiltro())
  params.set('page', '1')
  params.set('pageSize', '500')

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
const totalEsquecimento = computed(() => dadosFiltrados.value.filter(p => p.motivo === 'esquecimento').length)
const totalTransporte = computed(() => dadosFiltrados.value.filter(p => p.motivo === 'transporte').length)
const totalOutros = computed(() => dadosFiltrados.value.filter(p => p.motivo === 'outros').length)

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

const table = useTemplateRef('table')

const pagination = ref({
  pageIndex: 0,
  pageSize: 7
})

const colunas = [
  { accessorKey: 'paciente', header: 'Paciente' },
  { accessorKey: 'telefone', header: 'Telefone' },
  { accessorKey: 'dataFalta', header: 'Data da Falta' },
  { accessorKey: 'status', header: 'Status' },
  { id: 'acoes', header: 'Ações' }
]

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

function formatarData(iso: string) {
  const [ano, mes, dia] = iso.split('-')
  return `${dia}/${mes}/${ano}`
}

function ligar(paciente: PacienteNoShow) {
  console.log('Ligar para', paciente.nome, paciente.telefone)
}

function reagendar(paciente: PacienteNoShow) {
  console.log('Reagendar', paciente.nome)
}

function recusou(paciente: PacienteNoShow) {
  pacientesNoShow.value = pacientesNoShow.value.filter(p => p.id !== paciente.id)
}

onMounted(() => {
  carregarNoShow()
})
</script>

<template>
  <div>
    <UHeader title="No-show">
      <template #right>
        <div class="flex items-center gap-2">
          <UBadge
            :label="userName"
            color="neutral"
            variant="soft"
          />
          <UColorModeButton />
        </div>
      </template>
    </UHeader>
    <div class="p-6 space-y-8 bg-neutral-100 dark:bg-neutral-950 min-h-screen">
      <div class="w-full gap-4">
        <UCard class="w-full">
          <template #title>
            <p class="text-lg font-medium">
              Filtros de Análise
            </p>
          </template>
          <div class="space-y-4">
            <div class="flex flex-wrap items-end gap-4">
              <div class="flex items-end gap-2">
                <UFormField label="Ano">
                  <UInputMenu
                    v-model="filtroAno"
                    :items="anosDisponiveis"
                    placeholder="Ano"
                    size="sm"
                    class="w-24"
                  />
                </UFormField>
                <UFormField label="Mês início">
                  <UInputMenu
                    v-model="filtroMesInicio"
                    :items="mesesOpcoes"
                    placeholder="Mês início"
                    size="sm"
                    class="w-36"
                  />
                </UFormField>
                <span class="text-muted mb-1">até</span>
                <UFormField label="Mês fim">
                  <UInputMenu
                    v-model="filtroMesFim"
                    :items="mesesOpcoes"
                    placeholder="Mês fim"
                    size="sm"
                    class="w-36"
                  />
                </UFormField>
              </div>

              <UFormField label="Médico">
                <UInputMenu
                  v-model="filtroMedico"
                  :items="medicosOptions"
                  placeholder="Médico"
                  size="sm"
                  class="w-48"
                />
              </UFormField>
              <UFormField label="Especialidade">
                <UInputMenu
                  v-model="filtroEspecialidade"
                  :items="especialidadesOptions"
                  placeholder="Especialidade"
                  size="sm"
                  class="w-48"
                />
              </UFormField>
              <UFormField label="Convênio">
                <UInputMenu
                  v-model="filtroConvenio"
                  :items="conveniosOptions"
                  placeholder="Convênio"
                  size="sm"
                  class="w-48"
                />
              </UFormField>
              <UButton
                label="Aplicar Filtros"
                icon="i-lucide-filter"
                size="sm"
                color="primary"
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

      <div class="w-full grid grid-cols-5 items-center gap-4">
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
      <div class="w-full grid grid-cols-3 gap-4">
        <UCard class="col-span-1">
          <template #title>
            <p class="text-lg font-medium">
              Motivos de Falta
            </p>
          </template>
          <ChartMotivosFaltas
            :total="totalFiltrado"
            :esquecimento="totalEsquecimento"
            :transporte="totalTransporte"
            :outros="totalOutros"
          />
        </UCard>
        <UCard class="col-span-2">
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
      <div class="w-full grid grid-cols-3 gap-4">
        <UCard class="col-span-2">
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

      <div class="grid grid-cols-5 gap-4 items-stretch">
        <UCard
          :ui="{
            body: 'p-4 sm:p-4 sm:py-5 min-w-55 flex items-center h-full'
          }"
          class="col-span-2"
        >
          <div class="flex items-center gap-3 w-full">
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
            <div class="flex flex-col">
              <p class="text-sm font-bold text-nowrap">
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
          class="col-span-3"
        >
          <div class="flex items-center justify-between w-full">
            <div class="flex items-center gap-2">
              <UIcon
                name="i-lucide-download"
                class="text-primary size-5"
              />
              <span class="font-semibold">Exportar Dados</span>
            </div>
            <div class="flex items-center gap-3">
              <UButton
                icon="i-lucide-file-text"
                label="Exportar PDF"
                color="error"
                size="sm"
              />
              <UButton
                icon="i-lucide-file-spreadsheet"
                label="Exportar CSV"
                color="primary"
                size="sm"
              />
            </div>
          </div>
        </UCard>
      </div>

      <UCard class="w-full">
        <template #title>
          <div class="flex items-center justify-between">
            <p class="text-lg font-medium">
              Resgate de pacientes
            </p>
            <UInput
              v-model="filtro"
              placeholder="Filtrar por paciente ou telefone..."
              size="sm"
              class="w-72"
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

        <UTable
          v-else
          ref="table"
          v-model:pagination="pagination"
          :columns="colunas"
          :data="pacientesVisiveis"
          :pagination-options="{ getPaginationRowModel: getPaginationRowModel() }"
        >
          <template #paciente-cell="{ row }">
            <div class="flex items-center gap-3">
              <UAvatar
                :alt="row.original.nome"
                color="primary"
                size="sm"
              />
              <div>
                <p class="font-medium">
                  {{ row.original.nome }}
                </p>
                <p class="text-xs text-muted">
                  {{ row.original.convenio || 'Convênio não informado' }}
                </p>
              </div>
            </div>
          </template>

          <template #telefone-cell="{ row }">
            <span class="text-sm">{{ row.original.telefone || 'Não informado' }}</span>
          </template>

          <template #dataFalta-cell="{ row }">
            <span class="text-sm">{{ formatarData(row.original.dataFalta) }} {{ row.original.horario || '' }}</span>
          </template>

          <template #status-cell="{ row }">
            <UBadge
              :label="rotuloStatus(row.original.status)"
              :color="corStatus(row.original.status)"
              variant="subtle"
            />
          </template>

          <template #acoes-cell="{ row }">
            <div class="flex items-center gap-2">
              <UButton
                icon="i-lucide-phone"
                label="Ligar"
                size="sm"
                color="primary"

                @click="ligar(row.original)"
              />
              <UButton
                icon="i-lucide-calendar-plus"
                label="Reagendar"
                size="sm"
                color="warning"

                @click="reagendar(row.original)"
              />
              <UButton
                icon="i-lucide-x-circle"
                label="Recusou"
                size="sm"
                color="error"

                @click="pacienteRecusouSelecionado = row.original; modalRecusouAberto = true"
              />
              <UDropdownMenu :items="itensMais">
                <UButton
                  icon="lucide:menu"
                  label="Mais"
                  size="sm"
                  color="secondary"
                />
              </UDropdownMenu>
            </div>
          </template>
        </UTable>

        <div
          v-if="!loading && pacientesVisiveis.length"
          class="flex justify-center pt-4"
        >
          <UPagination
            :page="(table?.tableApi?.getState().pagination.pageIndex || 0) + 1"
            :items-per-page="table?.tableApi?.getState().pagination.pageSize || pagination.pageSize"
            :total="table?.tableApi?.getFilteredRowModel().rows.length || 0"
            @update:page="(p: number) => table?.tableApi?.setPageIndex(p - 1)"
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
  </div>
</template>
