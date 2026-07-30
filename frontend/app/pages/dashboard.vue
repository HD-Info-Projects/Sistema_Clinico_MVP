<script setup lang="ts">
import type { AgendamentoComPaciente, AgendamentoStatus } from '~/types'

const auth = useAuthStore()
const agendamentosStore = useAgendamentosStore()
const chamadosStore = useChamadosStore()
const { sala, precisaSelecionar, definirSala } = useSalaAtendimento()

const showSalaModal = ref(false)
const inputSala = ref('')

watch(showSalaModal, (val) => {
  if (val) inputSala.value = sala.value ?? ''
})

function confirmarSala() {
  if (inputSala.value) {
    definirSala(inputSala.value)
    showSalaModal.value = false
  }
}

onMounted(() => {
  const hoje = formatarDataISO(new Date())
  agendamentosStore.init(auth.activeClinicaId ?? undefined, hoje, auth.user?.id)
  chamadosStore.init()
  if (precisaSelecionar.value) {
    showSalaModal.value = true
  }
})

const userName = computed(() => auth.user?.nome || 'Usuário')

const { agora, dataFormatada } = useRelogio(60000)

const colunas = [
  { accessorKey: 'nome', header: 'Paciente', enableSorting: true },
  { accessorKey: 'horario', header: 'Horário' },
  { accessorKey: 'prioridade', header: 'Prioridade' },
  { accessorKey: 'status', header: 'Status' },
  { id: 'acoes', header: 'Ações' }
]

function corPrioridade(prioridade: string) {
  switch (prioridade) {
    case 'preferencial': return 'warning'
    default: return 'neutral'
  }
}

function corStatus(status: string) {
  switch (status) {
    case 'agendado': return 'secondary'
    case 'em-espera': return 'primary'
    case 'em-atendimento': return 'warning'
    case 'atendido': return 'success'
    case 'faltou': return 'error'
    default: return 'neutral'
  }
}

function rotuloStatus(status: string) {
  switch (status) {
    case 'agendado': return 'Agendado'
    case 'em-espera': return 'Em espera'
    case 'em-atendimento': return 'Em Atendimento'
    case 'atendido': return 'Atendido'
    case 'faltou': return 'Faltou'
    default: return status
  }
}

const callingState = ref<{ pacienteId: number, secondsLeft: number } | null>(null)
let callingInterval: ReturnType<typeof setInterval> | null = null

onUnmounted(() => {
  if (callingInterval) clearInterval(callingInterval)
})

function isTerminal(status: AgendamentoStatus) {
  return status === 'atendido' || status === 'faltou' || status === 'cancelado'
}

function isCalling(pacienteId: number) {
  return callingState.value?.pacienteId === pacienteId
}

const temPacienteEmAtendimento = computed(() => !!agendamentosStore.emAtendimento)

function chamarPaciente(ag: AgendamentoComPaciente) {
  if (!sala.value) {
    showSalaModal.value = true
    return
  }
  chamadosStore.chamarPaciente(ag.paciente.id, ag.paciente.nome, sala.value, auth.user?.nome ?? 'Dr.')
  if (callingInterval) clearInterval(callingInterval)
  callingState.value = { pacienteId: ag.paciente.id, secondsLeft: 5 }
  callingInterval = setInterval(() => {
    if (callingState.value && callingState.value.secondsLeft > 1) {
      callingState.value = { ...callingState.value, secondsLeft: callingState.value.secondsLeft - 1 }
    } else {
      callingState.value = null
      if (callingInterval) {
        clearInterval(callingInterval)
        callingInterval = null
      }
    }
  }, 500)
}

async function faltouAgendamento(ag: AgendamentoComPaciente) {
  try {
    await agendamentosStore.atualizarStatus(ag.id, 'faltou')
  } catch {
    console.error('Erro ao marcar falta')
  }
}

async function atenderAgendamento(ag: AgendamentoComPaciente) {
  try {
    await agendamentosStore.atualizarStatus(ag.id, 'em-atendimento')
    await navigateTo('/atendimento-medico')
  } catch {
    console.error('Erro ao iniciar atendimento')
  }
}

const pacientesNaFila = computed(() =>
  agendamentosStore.ordenados.filter(
    a => a.status === 'em-espera' || a.status === 'em-atendimento'
  )
)

const pacientesFinalizados = computed(() =>
  agendamentosStore.ordenados.filter(
    a => a.status === 'atendido' || a.status === 'faltou'
  )
)

const totalPacientesDashboard = computed(() =>
  pacientesNaFila.value.length + pacientesFinalizados.value.length
)

function statusLabel(status: AgendamentoStatus) {
  switch (status) {
    case 'em-atendimento': return 'Em Atendimento'
    case 'atendido': return 'Finalizado'
    default: return 'Atender'
  }
}

function statusColor(status: AgendamentoStatus) {
  switch (status) {
    case 'em-atendimento': return 'warning'
    case 'atendido': return 'success'
    default: return 'success'
  }
}

function atendimentoVariant(status: AgendamentoStatus) {
  switch (status) {
    case 'em-espera':
      return 'solid'
    default: return 'soft'
  }
}

function atendimentoDisabled(status: AgendamentoStatus) {
  return status !== 'em-espera'
}

const tempoMedioEspera = computed(() => {
  const lista = agendamentosStore.fila
  const tempos = lista.map(a => calcularMinutosDesde(a.horario, agora.value))
  return tempos.length ? Math.round(tempos.reduce((a, b) => a + b, 0) / tempos.length) : 0
})
</script>

<template>
  <div>
    <UHeader title="Dashboard">
      <template #right>
        <div class="flex items-center gap-2">
          <UBadge
            :label="userName"
            color="neutral"
            variant="soft"
          />
          <UBadge
            color="primary"
            variant="soft"
            class="cursor-pointer gap-1"
            @click="void (showSalaModal = true)"
          >
            Sala: {{ sala || '—' }}
            <UIcon
              name="i-lucide-pencil"
              class="h-3 w-3"
            />
          </UBadge>
          <UButton
            icon="i-lucide-bell"
            color="neutral"
            variant="ghost"
            size="lg"
            aria-label="Notificações"
          />
          <UButton
            icon="i-lucide-circle-help"
            color="neutral"
            variant="ghost"
            size="lg"
            aria-label="Ajuda"
          />
          <UColorModeButton />
        </div>
      </template>
    </UHeader>
    <div class="p-6 space-y-8 bg-neutral-100 dark:bg-neutral-950 min-h-screen">
      <div>
        <p class="text-3xl font-semibold text-foreground">
          {{ getSaudacao(agora) }}, Dr. {{ userName }}
        </p>
        <p class="text-base text-muted mt-1">
          {{ dataFormatada }}. Veja o resumo do dia.
        </p>
      </div>
      <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
        <ChartResumo
          :total="totalPacientesDashboard"
          :fila="agendamentosStore.fila.length"
          :em-atendimento="agendamentosStore.emAtendimento ? 1 : 0"
          :atendidos="agendamentosStore.totalAtendidos"
          :faltas="agendamentosStore.totalFaltas"
        />
        <div class="grid grid-cols-2 gap-2 items-center ">
          <UPageCard>
            <div class="flex flex-col gap-2 items-center">
              <div class="flex items-center gap-2">
                <div class="size-3 bg-warning rounded-full" />
                <p class="text-xl font-medium">
                  Tempo médio espera:
                </p>
              </div>
              <p class="text-3xl font-bold ">
                {{ tempoMedioEspera }} min.
              </p>
            </div>
          </UPageCard>
          <UPageCard>
            <div class="flex flex-col gap-2 items-center">
              <div class="flex items-center gap-2">
                <div class="size-3 bg-azu-500 rounded-full" />
                <p class="text-xl font-medium">
                  Em espera:
                </p>
              </div>
              <p class="text-3xl font-bold ">
                {{ agendamentosStore.fila.length }} Pessoa<span v-if="agendamentosStore.fila.length !== 1">s</span>
              </p>
            </div>
          </UPageCard>
          <UPageCard>
            <div class="flex flex-col gap-2 items-center">
              <div class="flex items-center gap-2">
                <div class="size-3 bg-success rounded-full" />
                <p class="text-xl font-medium">
                  Atendidos:
                </p>
              </div>
              <p class="text-3xl font-bold ">
                {{ agendamentosStore.totalAtendidos }} Pessoa<span v-if="agendamentosStore.totalAtendidos !== 1">s</span>
              </p>
            </div>
          </UPageCard>
          <UPageCard>
            <div class="flex flex-col gap-2 items-center">
              <div class="flex items-center gap-2">
                <div class="size-3 bg-error rounded-full" />
                <p class="text-xl font-medium">
                  Faltantes:
                </p>
              </div>
              <p class="text-3xl font-bold ">
                {{ agendamentosStore.totalFaltas }} Pessoa<span v-if="agendamentosStore.totalFaltas !== 1">s</span>
              </p>
            </div>
          </UPageCard>
        </div>
      </div>
      <UCard class="w-full">
        <template #title>
          <p class="text-lg font-medium">
            Pacientes na Fila de Espera
          </p>
        </template>

        <UTable
          :columns="colunas"
          :data="pacientesNaFila"
        >
          <template #nome-cell="{ row }">
            <div class="flex items-center gap-3">
              <UAvatar
                :alt="row.original.paciente.nome"
                color="primary"
                size="sm"
              />
              <div>
                <p class="font-medium">
                  {{ row.original.paciente.nome }}
                </p>
                <p class="text-xs text-muted">
                  {{ row.original.paciente.convenio }}
                </p>
              </div>
            </div>
          </template>

          <template #prioridade-cell="{ row }">
            <UBadge
              :label="row.original.prioridade"
              :color="corPrioridade(row.original.prioridade)"
              variant="subtle"
            />
          </template>

          <template #status-cell="{ row }">
            <UBadge
              :label="rotuloStatus(row.original.status)"
              :color="corStatus(row.original.status)"
              variant="subtle"
            />
          </template>

          <template #acoes-cell="{ row }">
            <div class="flex items-center gap-1">
              <UButton
                icon="i-lucide-phone"
                :label="isCalling(row.original.paciente.id) ? String(callingState!.secondsLeft) : 'Chamar'"
                size="sm"
                class="min-w-20"
                :color="isTerminal(row.original.status) ? 'neutral' : 'primary'"
                :variant="isTerminal(row.original.status) ? 'soft' : 'solid'"
                :loading="isCalling(row.original.paciente.id)"
                :disabled="temPacienteEmAtendimento || isTerminal(row.original.status) || isCalling(row.original.paciente.id)"
                @click="chamarPaciente(row.original as AgendamentoComPaciente)"
              />
              <UButton
                icon="i-lucide-user-x"
                label="Faltou"
                size="sm"
                :color="row.original.status === 'faltou' ? 'error' : (isTerminal(row.original.status) ? 'neutral' : 'error')"
                :variant="isTerminal(row.original.status) ? 'soft' : 'solid'"
                :disabled="temPacienteEmAtendimento || isTerminal(row.original.status) || isCalling(row.original.paciente.id)"
                @click="faltouAgendamento(row.original as AgendamentoComPaciente)"
              />
              <UButton
                :icon="row.original.status === 'atendido' ? 'i-lucide-check-circle' : 'i-lucide-user-check'"
                :label="statusLabel(row.original.status)"
                size="sm"
                :color="statusColor(row.original.status)"
                :variant="atendimentoVariant(row.original.status)"
                :disabled="temPacienteEmAtendimento || atendimentoDisabled(row.original.status) || isCalling(row.original.paciente.id)"
                @click="atenderAgendamento(row.original as AgendamentoComPaciente)"
              />
            </div>
          </template>
        </UTable>
      </UCard>

      <UCard class="w-full">
        <template #title>
          <p class="text-lg font-medium">
            Pacientes Atendidos / Faltas
          </p>
        </template>

        <UTable
          :columns="colunas.filter(c => c.id !== 'acoes')"
          :data="pacientesFinalizados"
        >
          <template #nome-cell="{ row }">
            <div class="flex items-center gap-3">
              <UAvatar
                :alt="row.original.paciente.nome"
                color="primary"
                size="sm"
              />
              <div>
                <p class="font-medium">
                  {{ row.original.paciente.nome }}
                </p>
                <p class="text-xs text-muted">
                  {{ row.original.paciente.convenio }}
                </p>
              </div>
            </div>
          </template>

          <template #prioridade-cell="{ row }">
            <UBadge
              :label="row.original.prioridade"
              :color="corPrioridade(row.original.prioridade)"
              variant="subtle"
            />
          </template>

          <template #status-cell="{ row }">
            <UBadge
              :label="rotuloStatus(row.original.status)"
              :color="corStatus(row.original.status)"
              variant="subtle"
            />
          </template>
        </UTable>
      </UCard>
    </div>
    <UModal
      v-model:open="showSalaModal"
      :close="false"
    >
      <template #header>
        <h2 class="text-lg font-semibold">
          Sala de Atendimento
        </h2>
      </template>

      <template #body>
        <div class="space-y-4">
          <p class="text-sm text-muted">
            Informe a sala de atendimento:
          </p>
          <UInput
            v-model="inputSala"
            placeholder="Ex: Consultório 2"
            size="lg"
          />
        </div>
      </template>

      <template #footer>
        <div class="flex justify-end gap-2">
          <UButton
            label="Salvar"
            :disabled="!inputSala"
            @click="confirmarSala"
          />
        </div>
      </template>
    </UModal>
  </div>
</template>
