<script setup lang="ts">
import type { AgendamentoComPaciente } from '~/types'
import { CalendarDate } from '@internationalized/date'

const openNav = inject<() => void>('openNav', () => {})
const agendamentosStore = useAgendamentosStore()
const auth = useAuthStore()

const selectedDate = ref(new Date())
const isPopoverOpen = ref(false)

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

function loadAgendamentos() {
  const dataStr = formatarDataISO(selectedDate.value)
  agendamentosStore.fetchAgendamentos(auth.activeClinicaId ?? undefined, dataStr, auth.user?.id)
}

function isToday(date: Date) {
  const today = new Date()
  return date.getDate() === today.getDate()
    && date.getMonth() === today.getMonth()
    && date.getFullYear() === today.getFullYear()
}

watch(selectedDate, loadAgendamentos)

onMounted(() => {
  loadAgendamentos()
})

const atendimentosOrdenados = computed(() => {
  return [...agendamentosStore.agendamentos].sort((a, b) => a.horario.localeCompare(b.horario))
})

const resumo = computed(() => ({
  agendados: agendamentosStore.agendamentos.filter(a => a.status === 'agendado').length,
  emEspera: agendamentosStore.agendamentos.filter(a => a.status === 'em-espera').length,
  emAtendimento: agendamentosStore.agendamentos.filter(a => a.status === 'em-atendimento').length,
  atendidos: agendamentosStore.agendamentos.filter(a => a.status === 'atendido').length,
  faltas: agendamentosStore.agendamentos.filter(a => a.status === 'faltou').length
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

function contatoPrincipal(atendimento: AgendamentoComPaciente) {
  const tel = textoInformado(atendimento.paciente.telefone)
  const email = textoInformado(atendimento.paciente.email)
  if (tel) return tel
  if (email) return email
  return 'Não informado'
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

      <UCard>
        <template #title>
          <div class="flex items-center justify-between">
            <p class="text-lg font-medium">
              Pacientes do Dia
            </p>
            <p class="text-sm text-muted">
              {{ agendamentosStore.agendamentos.length }} registro{{ agendamentosStore.agendamentos.length !== 1 ? 's' : '' }}
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
            class="grid grid-cols-1 gap-3 rounded-lg border border-muted p-3 md:grid-cols-5"
          >
            <USkeleton class="h-5 w-16" />
            <div class="col-span-2 space-y-2">
              <USkeleton class="h-5 w-48 max-w-full" />
              <USkeleton class="h-4 w-32 max-w-full" />
            </div>
            <USkeleton class="h-5 w-36 max-w-full" />
            <USkeleton class="h-6 w-24 rounded-full" />
          </div>
        </div>

        <p
          v-else-if="!agendamentosStore.agendamentos.length"
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
            <div class="grid grid-cols-2 md:grid-cols-5 gap-x-4 gap-y-3 items-start md:items-center">
              <div class="col-span-2">
                <p class="text-sm text-muted font-bold text-center sm:text-left">
                  Paciente
                </p>
                <div class="flex items-center gap-3 justify-center">
                  <UAvatar
                    :alt="item.paciente.nome"
                    color="primary"
                    size="sm"
                  />
                  <div>
                    <p class="font-medium">
                      {{ item.paciente.nome || 'Paciente não informado' }}
                    </p>
                    <p class="text-xs text-muted">
                      {{ textoInformado(idadePaciente(item.paciente.dataNascimento)) ? `${idadePaciente(item.paciente.dataNascimento)}` : '' }}
                      {{ textoNaoInformado(item.paciente.convenio, '') ? `· ${item.paciente.convenio}` : '' }}
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
                    {{ textoNaoInformado(item.paciente.email, '') || '' }}
                  </p>
                </div>
              </div>

              <div class="col-span-2 md:col-span-1 text-center">
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
