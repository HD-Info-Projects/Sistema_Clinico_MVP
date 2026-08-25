<script setup lang="ts">
import type { TipoProcedimentoTuss } from '~/types'
import { CalendarDate } from '@internationalized/date'
import { TUSS_PROCEDIMENTO_FILTROS, corTipoProcedimento, rotuloTipoProcedimento } from '~/utils/tuss'

const openNav = inject<() => void>('openNav', () => {})

interface ItemRecepcao {
  id: number | string
  horario: string
  paciente: string
  dataNascimento: string | null
  convenio: string
  telefone: string
  celular: string
  email: string
  medico: string
  crm: string
  crmAtendimento: string
  especialidade: string
  codigoProcedimentoSpdata: string | null
  tipoProcedimento: TipoProcedimentoTuss
  tipoProcedimentoLabel: string
  status: string
}

interface CheckInResponse {
  items: ItemRecepcao[]
}

const auth = useAuthStore()

const selectedDate = ref(new Date())
const isPopoverOpen = ref(false)
const agendamentos = ref<ItemRecepcao[]>([])
const loading = ref(true)
const errorMsg = ref('')
const selectedMedico = ref('Todos')
const selectedEspecialidade = ref('Todos')
const selectedStatus = ref('')
const selectedTipo = ref<TipoProcedimentoTuss | ''>('')
let requestId = 0

const formattedDate = computed(() => {
  const d = selectedDate.value
  const diaSemana = formatarDiaDaSemana(d)
  return `${d.toLocaleDateString('pt-BR')} - ${diaSemana}`
})

const calendarDate = computed({
  get: () => {
    const d = selectedDate.value
    return new CalendarDate(d.getFullYear(), d.getMonth() + 1, d.getDate())
  },
  set: (val: CalendarDate) => {
    selectedDate.value = new Date(val.year, val.month - 1, val.day)
  }
})

function prevDay() {
  const d = new Date(selectedDate.value)
  d.setDate(d.getDate() - 1)
  selectedDate.value = d
}

function nextDay() {
  const d = new Date(selectedDate.value)
  d.setDate(d.getDate() + 1)
  selectedDate.value = d
}

function goToToday() {
  selectedDate.value = new Date()
  isPopoverOpen.value = false
}

function isToday(date: Date) {
  const today = new Date()
  return date.getDate() === today.getDate()
    && date.getMonth() === today.getMonth()
    && date.getFullYear() === today.getFullYear()
}

async function loadAgendamentos() {
  const currentRequest = ++requestId
  const dataStr = formatarDataISO(selectedDate.value)
  const unidadeId = auth.activeClinicaId
  loading.value = true
  errorMsg.value = ''

  if (!unidadeId) {
    agendamentos.value = []
    errorMsg.value = 'Selecione uma unidade para carregar agendamentos'
    loading.value = false
    return
  }

  const params = new URLSearchParams()
  params.set('data', dataStr)
  params.set('pageSize', '100')
  params.set('unidadeId', String(unidadeId))
  if (selectedTipo.value) params.set('tipo', selectedTipo.value)

  try {
    const response = await $fetch<CheckInResponse>(`/api/check-in?${params.toString()}`)
    if (currentRequest === requestId) agendamentos.value = response.items ?? []
  } catch {
    if (currentRequest === requestId) {
      agendamentos.value = []
      errorMsg.value = 'Erro ao carregar agendamentos'
    }
  } finally {
    if (currentRequest === requestId) loading.value = false
  }
}

watch(selectedDate, loadAgendamentos)
watch(() => auth.activeClinicaId, () => {
  selectedMedico.value = 'Todos'
  selectedEspecialidade.value = 'Todos'
  selectedTipo.value = ''
  loadAgendamentos()
})

onMounted(() => {
  loadAgendamentos()
})

const medicosOpcoes = computed(() => {
  const nomes = agendamentos.value
    .map(a => textoInformado(a.medico))
    .filter(Boolean)
  return ['Todos', ...Array.from(new Set(nomes)).sort((a, b) => a.localeCompare(b, 'pt-BR'))]
})

const especialidadesOpcoes = computed(() => {
  const especialidades = agendamentos.value
    .map(a => textoInformado(a.especialidade))
    .filter(Boolean)
  return ['Todos', ...Array.from(new Set(especialidades)).sort((a, b) => a.localeCompare(b, 'pt-BR'))]
})

const filtrosStatus = [
  { label: 'Todos', value: '' },
  { label: 'Agendados', value: 'agendado' },
  { label: 'Em espera', value: 'em-espera' },
  { label: 'Em atendimento', value: 'em-atendimento' },
  { label: 'Atendidos', value: 'atendido' },
  { label: 'Faltosos', value: 'faltou' }
]

const filtrosTipo = TUSS_PROCEDIMENTO_FILTROS

const atendimentosFiltrados = computed(() => {
  return agendamentos.value.filter((a) => {
    if (selectedMedico.value !== 'Todos' && a.medico !== selectedMedico.value) return false
    if (selectedEspecialidade.value !== 'Todos' && a.especialidade !== selectedEspecialidade.value) return false
    if (selectedStatus.value && a.status !== selectedStatus.value) return false
    if (selectedTipo.value && a.tipoProcedimento !== selectedTipo.value) return false
    return true
  })
})

const atendimentosOrdenados = computed(() => {
  return [...atendimentosFiltrados.value].sort((a, b) => a.horario.localeCompare(b.horario))
})

const resumo = computed(() => ({
  agendados: atendimentosFiltrados.value.filter(a => a.status === 'agendado').length,
  emEspera: atendimentosFiltrados.value.filter(a => a.status === 'em-espera').length,
  emAtendimento: atendimentosFiltrados.value.filter(a => a.status === 'em-atendimento').length,
  atendidos: atendimentosFiltrados.value.filter(a => a.status === 'atendido').length,
  faltas: atendimentosFiltrados.value.filter(a => a.status === 'faltou').length
}))

function idadePaciente(dataNascimento: string | null | undefined) {
  if (!dataNascimento) return ''
  const data = new Date(dataNascimento)
  if (Number.isNaN(data.getTime())) return ''
  const hoje = new Date()
  let idade = hoje.getFullYear() - data.getFullYear()
  const aniversario = new Date(hoje.getFullYear(), data.getMonth(), data.getDate())
  if (aniversario > hoje) idade -= 1
  if (idade < 0) return ''
  return idade === 1 ? '1 ano' : `${idade} anos`
}

function textoInformado(valor: string | number | null | undefined) {
  const texto = String(valor ?? '').trim()
  return texto && texto !== '0' ? texto : ''
}

function textoNaoInformado(valor: string | number | null | undefined, fallback = 'Não informado') {
  return textoInformado(valor) || fallback
}

function contatoPrincipal(item: ItemRecepcao) {
  const tel = textoInformado(item.telefone)
  const celular = textoInformado(item.celular)
  const email = textoInformado(item.email)
  if (tel) return tel
  if (celular) return celular
  if (email) return email
  return 'Não informado'
}

function crmExibicao(item: ItemRecepcao) {
  return textoInformado(item.crmAtendimento) || textoInformado(item.crm)
}

function corStatus(s: string) {
  switch (s) {
    case 'agendado': return 'secondary'
    case 'em-espera': return 'primary'
    case 'em-atendimento': return 'warning'
    case 'atendido': return 'success'
    case 'faltou': return 'error'
    default: return 'neutral'
  }
}

function rotuloStatus(s: string) {
  switch (s) {
    case 'agendado': return 'Agendado'
    case 'em-espera': return 'Em espera'
    case 'em-atendimento': return 'Em atendimento'
    case 'atendido': return 'Atendido'
    case 'faltou': return 'Faltou'
    default: return 'Desconhecido'
  }
}

function corTipo(tipo: string) {
  return corTipoProcedimento(tipo)
}

function rotuloTipo(item: ItemRecepcao) {
  return rotuloTipoProcedimento(item.tipoProcedimento, item.tipoProcedimentoLabel)
}

function selecionarTipo(tipo: TipoProcedimentoTuss | '' | null | undefined) {
  selectedTipo.value = tipo ?? ''
  loadAgendamentos()
}

const statuses: { id: string, name: string, color: string }[] = [
  { id: 'agendado', name: 'Agendado', color: 'secondary' },
  { id: 'em-espera', name: 'Em espera', color: 'primary' },
  { id: 'em-atendimento', name: 'Em atendimento', color: 'warning' },
  { id: 'atendido', name: 'Atendido', color: 'success' },
  { id: 'faltou', name: 'Falta', color: 'error' }
]
</script>

<template>
  <div>
    <UHeader
      title="Agenda - Recepção"
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
      <div class="flex gap-4">
        <div
          v-for="s in statuses"
          :key="s.id"
          class="flex items-center gap-1.5 text-sm"
        >
          <div :class="`size-2.5 rounded-full bg-${s.color}`" />
          {{ s.name }}
        </div>
      </div>
      <template #right>
        <UColorModeButton />
      </template>
    </UHeader>

    <div class="min-h-screen space-y-4 bg-muted p-4 sm:space-y-6 sm:p-6">
      <div class="flex flex-wrap items-center gap-2">
        <UInputMenu
          v-model="selectedMedico"
          :items="medicosOpcoes"
          size="sm"
          class="w-full sm:w-56"
        />
        <UInputMenu
          v-model="selectedEspecialidade"
          :items="especialidadesOpcoes"
          size="sm"
          class="w-full sm:w-56"
        />
        <div class="flex flex-wrap gap-2">
          <UButton
            v-for="status in filtrosStatus"
            :key="status.value || 'todos'"
            :label="status.label"
            :color="status.value ? corStatus(status.value) : 'neutral'"
            :variant="selectedStatus === status.value ? 'solid' : 'soft'"
            size="sm"
            @click="void (selectedStatus = status.value)"
          />
        </div>
        <USelectMenu
          :model-value="selectedTipo || undefined"
          :items="filtrosTipo"
          value-key="value"
          label-key="label"
          placeholder="Filtrar por tipo"
          clearable
          size="sm"
          class="w-full sm:w-56"
          @update:model-value="selecionarTipo"
        />
      </div>

      <div class="flex items-center justify-between">
        <UButton
          icon="i-lucide-chevron-left"
          color="neutral"
          variant="ghost"
          size="lg"
          @click="prevDay"
        />
        <div class="flex items-center gap-4">
          <UPopover v-model:open="isPopoverOpen">
            <UButton
              color="neutral"
              variant="link"
              class="text-lg font-semibold"
            >
              {{ formattedDate }} {{ isToday(selectedDate) ? '(Hoje)' : '' }}
            </UButton>
            <template #content>
              <div class="p-2">
                <UCalendar v-model="calendarDate" />
                <UButton
                  label="Hoje"
                  color="primary"
                  variant="soft"
                  size="sm"
                  class="mt-2 w-full"
                  @click="goToToday"
                />
              </div>
            </template>
          </UPopover>
        </div>
        <UButton
          icon="i-lucide-chevron-right"
          color="neutral"
          variant="ghost"
          size="lg"
          @click="nextDay"
        />
      </div>

      <div class="flex flex-wrap gap-2">
        <UBadge
          :label="`${resumo.agendados} agendados`"
          color="warning"
          variant="subtle"
        />
        <UBadge
          :label="`${resumo.emEspera} em espera`"
          color="primary"
          variant="subtle"
        />
        <UBadge
          :label="`${resumo.emAtendimento} em atendimento`"
          color="warning"
          variant="subtle"
        />
        <UBadge
          :label="`${resumo.atendidos} atendidos`"
          color="success"
          variant="subtle"
        />
        <UBadge
          :label="`${resumo.faltas} faltas`"
          color="error"
          variant="subtle"
        />
      </div>

      <UAlert
        v-if="errorMsg"
        :title="errorMsg"
        color="error"
        variant="subtle"
        icon="i-lucide-circle-alert"
      />

      <UCard>
        <template #title>
          <div class="flex items-center justify-between">
            <p class="text-lg font-medium">
              Pacientes do Dia
            </p>
            <p class="text-sm text-muted">
              {{ atendimentosFiltrados.length }} registro{{ atendimentosFiltrados.length !== 1 ? 's' : '' }}
            </p>
          </div>
        </template>

        <div
          v-if="loading"
          class="space-y-3 py-4"
        >
          <div
            v-for="linha in 5"
            :key="linha"
            class="grid grid-cols-1 gap-3 rounded-lg border border-muted p-3 md:grid-cols-[80px_1.5fr_1fr_1fr_120px_120px]"
          >
            <USkeleton class="h-5 w-16" />
            <div class="col-span-2 space-y-2">
              <USkeleton class="h-5 w-48 max-w-full" />
              <USkeleton class="h-4 w-32 max-w-full" />
            </div>
            <USkeleton class="h-5 w-36 max-w-full" />
            <USkeleton class="h-5 w-40 max-w-full" />
            <USkeleton class="h-6 w-24 rounded-full" />
            <USkeleton class="h-6 w-24 rounded-full" />
          </div>
        </div>

        <p
          v-else-if="!atendimentosFiltrados.length"
          class="text-sm text-muted py-4"
        >
          Nenhum paciente agendado para esta data.
        </p>

        <div
          v-else
          class="flex flex-col gap-2"
        >
          <UPageCard
            v-for="item in atendimentosOrdenados"
            :key="item.id"
            :ui="{ container: 'p-1 sm:p-1' }"
          >
            <div class="grid grid-cols-2 md:grid-cols-7 gap-x-4 gap-y-3 items-start md:items-center">
              <div class="col-span-2">
                <p class="text-sm text-muted font-bold text-center sm:text-left">
                  Paciente
                </p>
                <div class="flex items-center gap-3 justify-center">
                  <UAvatar
                    :alt="item.paciente"
                    color="primary"
                    size="sm"
                  />
                  <div>
                    <p class="font-medium">
                      {{ item.paciente || 'Paciente não informado' }}
                    </p>
                    <p class="text-xs text-muted">
                      {{ textoInformado(idadePaciente(item.dataNascimento)) ? idadePaciente(item.dataNascimento) : '' }}
                      {{ textoNaoInformado(item.convenio, '') ? `· ${item.convenio}` : '' }}
                    </p>
                  </div>
                </div>
              </div>

              <div class="md:col-span-1 text-center">
                <p class="text-sm text-muted font-bold">
                  Horário
                </p>
                <p class="whitespace-nowrap font-mono text-sm">
                  {{ item.horario || '-' }}
                </p>
              </div>

              <div class="md:col-span-1 text-center">
                <p class="text-sm text-muted font-bold">
                  Contato
                </p>
                <div class="text-sm">
                  <p>{{ contatoPrincipal(item) }}</p>
                  <p class="text-xs text-muted">
                    {{ textoNaoInformado(item.email, '') || '' }}
                  </p>
                </div>
              </div>

              <div class="md:col-span-1 text-center">
                <p class="text-sm text-muted font-bold">
                  Médico
                </p>
                <div class="text-sm">
                  <p class="font-medium">
                    {{ item.medico || '-' }}
                  </p>
                  <p class="text-xs text-muted">
                    {{ textoNaoInformado(crmExibicao(item), 'CRM não informado') }}
                  </p>
                </div>
              </div>

              <div class="md:col-span-1 text-center">
                <p class="text-sm text-muted font-bold">
                  Tipo
                </p>
                <UBadge
                  :label="rotuloTipo(item)"
                  :color="corTipo(item.tipoProcedimento)"
                  variant="subtle"
                />
                <p
                  v-if="item.codigoProcedimentoSpdata"
                  class="mt-1 text-xs text-muted"
                >
                  TUSS {{ item.codigoProcedimentoSpdata }}
                </p>
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
            </div>
          </UPageCard>
        </div>
      </UCard>
    </div>
  </div>
</template>
