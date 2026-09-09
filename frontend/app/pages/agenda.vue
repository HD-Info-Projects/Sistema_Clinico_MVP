<script setup lang="ts">
import type { AgendamentoComPaciente, AgendamentoStatus } from '~/types'
import type { DateValue } from '@internationalized/date'
import { CalendarDate } from '@internationalized/date'
import { corTipoProcedimento, rotuloTipoProcedimento } from '~/utils/tuss'

const openNav = inject<() => void>('openNav', () => {})

type MarcadorStatus = Exclude<AgendamentoStatus, 'cancelado'>
type MarcadorCalendarioResponse = {
  data?: string | null
  status?: AgendamentoStatus[] | AgendamentoStatus | null
}

const ordemMarcadoresStatus: MarcadorStatus[] = [
  'agendado',
  'em-espera',
  'em-atendimento',
  'atendido',
  'faltou'
]
const classesPontoStatus: Record<MarcadorStatus, string> = {
  'agendado': 'bg-secondary',
  'em-espera': 'bg-primary',
  'em-atendimento': 'bg-warning',
  'atendido': 'bg-success',
  'faltou': 'bg-error'
}
const agendamentosStore = useAgendamentosStore()
const auth = useAuthStore()

const selectedDate = ref(new Date())
const calendarPlaceholder = shallowRef(dateToCalendarDate(selectedDate.value))
const isPopoverOpen = ref(false)
const marcadoresCalendario = ref<Record<string, MarcadorStatus[]>>({})
const cacheMarcadoresCalendario = new Map<
  string,
  Record<string, MarcadorStatus[]>
>()
let marcadoresRequestId = 0

function dateToCalendarDate(d: Date) {
  return new CalendarDate(d.getFullYear(), d.getMonth() + 1, d.getDate())
}

function dataISOCalendar(date: DateValue) {
  const month = String(date.month).padStart(2, '0')
  const day = String(date.day).padStart(2, '0')
  return `${date.year}-${month}-${day}`
}

function chaveMesCalendar(date: DateValue) {
  return `${date.year}-${String(date.month).padStart(2, '0')}`
}

function chaveCacheMarcadores(date: DateValue) {
  return `${auth.activeClinicaId ?? 'sem-unidade'}:${chaveMesCalendar(date)}`
}

function intervaloMes(date: DateValue) {
  const inicio = new Date(date.year, date.month - 1, 1)
  const fim = new Date(date.year, date.month, 0)
  return {
    dataIni: formatarDataISO(inicio),
    dataFim: formatarDataISO(fim)
  }
}

function isMarcadorStatus(status: unknown): status is MarcadorStatus {
  return ordemMarcadoresStatus.includes(status as MarcadorStatus)
}

function montarMarcadoresCalendario(items: MarcadorCalendarioResponse[]) {
  const statusPorData = new Map<string, Set<MarcadorStatus>>()

  for (const item of items) {
    const data = String(item.data ?? '').slice(0, 10)
    if (!data) continue

    const statusDia = statusPorData.get(data) ?? new Set<MarcadorStatus>()
    const statusItem = Array.isArray(item.status) ? item.status : [item.status]
    for (const status of statusItem) {
      if (isMarcadorStatus(status)) statusDia.add(status)
    }
    if (statusDia.size) statusPorData.set(data, statusDia)
  }

  return Object.fromEntries(
    Array.from(statusPorData.entries()).map(([data, statusDia]) => [
      data,
      ordemMarcadoresStatus.filter(status => statusDia.has(status))
    ])
  )
}

function marcadoresDoDia(day: DateValue) {
  return marcadoresCalendario.value[dataISOCalendar(day)] ?? []
}

const formattedDate = computed(() => {
  const d = selectedDate.value
  const diaSemana = formatarDiaDaSemana(d)
  return `${d.toLocaleDateString('pt-BR')} - ${diaSemana}`
})

const calendarDate = computed({
  get: () => {
    return dateToCalendarDate(selectedDate.value)
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

function loadAgendamentos() {
  const dataStr = formatarDataISO(selectedDate.value)
  agendamentosStore.fetchAgendamentos(
    auth.activeClinicaId ?? undefined,
    dataStr,
    auth.user?.id
  )
}

async function buscarMarcadoresCalendario(
  date: DateValue,
  sincronizar = false
) {
  const { dataIni, dataFim } = intervaloMes(date)
  const params = new URLSearchParams({ dataIni, dataFim })
  if (auth.activeClinicaId)
    params.set('clinicaId', String(auth.activeClinicaId))
  if (sincronizar) params.set('sincronizar', 'true')

  const items = await $fetch<MarcadorCalendarioResponse[]>(
    `/api/agendamentos/marcadores?${params.toString()}`
  )
  return montarMarcadoresCalendario(items)
}

async function atualizarMarcadoresCalendario(
  date: DateValue,
  requestId: number
) {
  try {
    const marcadoresAtualizados = await buscarMarcadoresCalendario(date, true)
    if (requestId !== marcadoresRequestId) return

    cacheMarcadoresCalendario.set(
      chaveCacheMarcadores(date),
      marcadoresAtualizados
    )
    marcadoresCalendario.value = marcadoresAtualizados
  } catch {
    // Mantém os marcadores locais/cacheados se a sincronização em segundo plano falhar.
  }
}

async function loadMarcadoresCalendario(date = calendarPlaceholder.value) {
  const requestId = ++marcadoresRequestId
  const chaveCache = chaveCacheMarcadores(date)
  const marcadoresCache = cacheMarcadoresCalendario.get(chaveCache)
  marcadoresCalendario.value = marcadoresCache ?? {}

  try {
    const marcadoresLocais = await buscarMarcadoresCalendario(date)
    if (requestId !== marcadoresRequestId) return

    cacheMarcadoresCalendario.set(chaveCache, marcadoresLocais)
    marcadoresCalendario.value = marcadoresLocais
  } catch {
    if (requestId === marcadoresRequestId && !marcadoresCache)
      marcadoresCalendario.value = {}
  }

  void atualizarMarcadoresCalendario(date, requestId)
}

function isToday(date: Date) {
  const today = new Date()
  return (
    date.getDate() === today.getDate()
    && date.getMonth() === today.getMonth()
    && date.getFullYear() === today.getFullYear()
  )
}

watch(selectedDate, () => {
  loadAgendamentos()

  const novoPlaceholder = dateToCalendarDate(selectedDate.value)
  if (
    chaveMesCalendar(novoPlaceholder)
    !== chaveMesCalendar(calendarPlaceholder.value)
  ) {
    calendarPlaceholder.value = novoPlaceholder
  }
})

watch(calendarPlaceholder, (placeholder, anterior) => {
  if (
    !anterior
    || chaveMesCalendar(placeholder) !== chaveMesCalendar(anterior)
  ) {
    loadMarcadoresCalendario(placeholder)
  }
})

onMounted(() => {
  loadAgendamentos()
  loadMarcadoresCalendario()
})

const atendimentosFiltrados = computed(() => agendamentosStore.agendamentos)

const atendimentosOrdenados = computed(() => {
  return [...atendimentosFiltrados.value].sort((a, b) =>
    a.horario.localeCompare(b.horario)
  )
})

const resumo = computed(() => ({
  agendados: atendimentosFiltrados.value.filter(a => a.status === 'agendado')
    .length,
  emEspera: atendimentosFiltrados.value.filter(a => a.status === 'em-espera')
    .length,
  emAtendimento: atendimentosFiltrados.value.filter(
    a => a.status === 'em-atendimento'
  ).length,
  atendidos: atendimentosFiltrados.value.filter(a => a.status === 'atendido')
    .length,
  faltas: atendimentosFiltrados.value.filter(a => a.status === 'faltou')
    .length
}))

function idadePaciente(dataNascimento: string | null | undefined) {
  if (!dataNascimento) return ''
  const data = new Date(dataNascimento)
  if (Number.isNaN(data.getTime())) return ''
  const hoje = new Date()
  let idade = hoje.getFullYear() - data.getFullYear()
  const aniversario = new Date(
    hoje.getFullYear(),
    data.getMonth(),
    data.getDate()
  )
  if (aniversario > hoje) idade -= 1
  if (idade < 0) return ''
  return idade === 1 ? '1 ano' : `${idade} anos`
}

function textoInformado(valor: string | number | null | undefined) {
  const texto = String(valor ?? '').trim()
  return texto && texto !== '0' ? texto : ''
}

function textoNaoInformado(
  valor: string | number | null | undefined,
  fallback = 'Não informado'
) {
  return textoInformado(valor) || fallback
}

function contatoPrincipal(atendimento: AgendamentoComPaciente) {
  const tel = textoInformado(atendimento.paciente.telefone)
  const email = textoInformado(atendimento.paciente.email)
  if (tel) return tel
  if (email) return email
  return 'Não informado'
}

function corStatus(s: string) {
  switch (s) {
    case 'agendado':
      return 'secondary'
    case 'em-espera':
      return 'primary'
    case 'em-atendimento':
      return 'warning'
    case 'atendido':
      return 'success'
    case 'faltou':
      return 'error'
    default:
      return 'neutral'
  }
}

function rotuloStatus(s: string) {
  switch (s) {
    case 'agendado':
      return 'Agendado'
    case 'em-espera':
      return 'Em espera'
    case 'em-atendimento':
      return 'Em atendimento'
    case 'atendido':
      return 'Atendido'
    case 'faltou':
      return 'Faltou'
    default:
      return 'Desconhecido'
  }
}

function corTipo(tipo: string | null | undefined) {
  return corTipoProcedimento(tipo)
}

function rotuloTipo(item: AgendamentoComPaciente) {
  return rotuloTipoProcedimento(
    item.tipoProcedimento,
    item.tipoProcedimentoLabel
  )
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
      title="Agenda de Consultas"
      toggle-side="left"
    >
      <template #toggle>
        <UButton
          icon="i-lucide-menu"
          color="neutral"
          variant="ghost"
          class="min-h-11 min-w-11 lg:hidden"
          aria-label="Abrir menu"
          @click="openNav()"
        />
      </template>
      <div class="hidden flex-wrap justify-center gap-x-4 gap-y-1 xl:flex">
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

    <div
      class="min-h-screen min-w-0 space-y-4 bg-muted p-3 sm:space-y-6 sm:p-6"
    >
      <div
        class="grid grid-cols-[2.5rem_minmax(0,1fr)_2.5rem] items-center gap-1 sm:gap-3"
      >
        <UButton
          icon="i-lucide-chevron-left"
          color="neutral"
          variant="ghost"
          size="lg"
          class="min-h-10 min-w-10"
          @click="prevDay"
        />
        <div class="min-w-0 text-center">
          <UPopover v-model:open="isPopoverOpen">
            <UButton
              color="neutral"
              variant="link"
              class="h-auto max-w-full whitespace-normal px-1 text-center text-sm font-semibold leading-snug sm:text-lg"
            >
              {{ formattedDate }} {{ isToday(selectedDate) ? "(Hoje)" : "" }}
            </UButton>
            <template #content>
              <div class="p-2">
                <UCalendar
                  v-model="calendarDate"
                  v-model:placeholder="calendarPlaceholder"
                  size="lg"
                >
                  <template #day="{ day }">
                    <span
                      class="relative flex size-full items-center justify-center"
                    >
                      <span>{{ day.day }}</span>
                      <span
                        v-if="marcadoresDoDia(day).length"
                        class="absolute bottom-0.5 left-1/2 flex -translate-x-1/2 gap-0.5"
                      >
                        <span
                          v-for="status in marcadoresDoDia(day)"
                          :key="status"
                          :class="[
                            'size-1 rounded-full',
                            classesPontoStatus[status]
                          ]"
                        />
                      </span>
                    </span>
                  </template>
                </UCalendar>
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
          class="min-h-10 min-w-10"
          @click="nextDay"
        />
      </div>

      <div class="flex flex-wrap justify-center gap-2 sm:justify-start">
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

      <UCard>
        <template #title>
          <div
            class="flex flex-col gap-1 sm:flex-row sm:items-center sm:justify-between"
          >
            <p class="text-lg font-medium">
              Pacientes do Dia
            </p>
            <p class="text-sm text-muted">
              {{ atendimentosFiltrados.length }} registro{{
                atendimentosFiltrados.length !== 1 ? "s" : ""
              }}
            </p>
          </div>
        </template>

        <div
          v-if="agendamentosStore.loading"
          class="space-y-3 py-4"
        >
          <div
            v-for="linha in 5"
            :key="linha"
            class="grid grid-cols-1 gap-3 rounded-lg border border-muted p-3 sm:grid-cols-2 md:grid-cols-6 md:items-center"
          >
            <div class="space-y-2 sm:col-span-2">
              <USkeleton class="h-5 w-48 max-w-full" />
              <USkeleton class="h-4 w-32 max-w-full" />
            </div>
            <USkeleton class="mx-auto h-5 w-16 md:mx-0" />
            <USkeleton class="h-5 w-36 max-w-full" />
            <USkeleton
              class="mx-auto h-6 w-32 max-w-full rounded-full md:mx-0"
            />
            <USkeleton class="mx-auto h-6 w-24 rounded-full md:mx-0" />
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
            variant="ghost"
            class="border-b border-muted rounded-none"
            :ui="{ container: 'px-4 sm:p-1 pb-3 sm:px-4' }"
          >
            <div
              class="grid min-w-0 grid-cols-1 gap-x-4 gap-y-3 sm:grid-cols-2 md:grid-cols-[max-content_2fr_1.5fr_1fr_1fr] md:items-center"
            >
              <div class="hidden w-min pr-3 md:block">
                <p class="text-sm text-muted font-bold">
                  Horário
                </p>
                <p class="whitespace-nowrap pt-2 font-mono text-sm">
                  {{ item.horario || "-" }}
                </p>
              </div>

              <div class="sm:col-span-2 md:col-span-1">
                <p class="text-sm text-muted font-bold">
                  Paciente
                </p>
                <div class="flex min-w-0 items-center gap-3">
                  <UAvatar
                    :alt="item.paciente.nome"
                    color="primary"
                    size="sm"
                  />
                  <div class="min-w-0">
                    <p class="wrap-break-word font-medium">
                      {{ item.paciente.nome || "Paciente não informado" }}
                    </p>
                    <p class="wrap-break-word text-xs text-muted">
                      {{
                        textoInformado(
                          idadePaciente(item.paciente.dataNascimento)
                        )
                          ? `${idadePaciente(item.paciente.dataNascimento)}`
                          : ""
                      }}
                      {{
                        textoNaoInformado(item.paciente.convenio, "")
                          ? `· ${item.paciente.convenio}`
                          : ""
                      }}
                    </p>
                  </div>
                </div>
              </div>

              <div class="sm:col-span-2 md:col-span-1">
                <p class="text-sm text-muted font-bold">
                  Contato
                </p>
                <div class="min-w-0 text-sm">
                  <p class="break-all">
                    {{ contatoPrincipal(item) }}
                  </p>
                  <p class="break-all text-xs text-muted">
                    {{ textoNaoInformado(item.paciente.email, "") || "" }}
                  </p>
                </div>
              </div>

              <div class="block md:hidden">
                <p class="text-sm text-muted font-bold">
                  Horário
                </p>
                <p class="whitespace-nowrap pt-2 font-mono text-sm">
                  {{ item.horario || "-" }}
                </p>
              </div>

              <div class="text-left">
                <p class="text-sm text-muted font-bold">
                  Tipo de Atend.
                </p>
                <UBadge
                  :label="rotuloTipo(item)"
                  :color="corTipo(item.tipoProcedimento)"
                  variant="subtle"
                  class="md:max-w-40 break-all cursor-default"
                />
              </div>

              <div class="text-left">
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
