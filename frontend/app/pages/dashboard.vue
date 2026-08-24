<script setup lang="ts">
import type { AgendamentoComPaciente, AgendamentoStatus } from '~/types'
import { corTipoProcedimento, rotuloTipoProcedimento } from '~/utils/tuss'

const auth = useAuthStore()
const agendamentosStore = useAgendamentosStore()
const chamadosStore = useChamadosStore()
const toast = useToast()
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
  chamadosStore.init({ clinicaId: auth.activeClinicaId, data: hoje })
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
  { accessorKey: 'tipoProcedimento', header: 'Tipo' },
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

function corTipo(tipo: string | null | undefined) {
  return corTipoProcedimento(tipo)
}

function rotuloTipo(ag: AgendamentoComPaciente) {
  return rotuloTipoProcedimento(ag.tipoProcedimento, ag.tipoProcedimentoLabel)
}

const callingState = ref<{ pacienteId: number, secondsLeft: number } | null>(null)
const chamadaEmEnvio = ref<number | null>(null)
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

function isChamadaBloqueada(pacienteId: number) {
  return chamadaEmEnvio.value === pacienteId || isCalling(pacienteId)
}

function rotuloChamada(pacienteId: number) {
  if (chamadaEmEnvio.value === pacienteId) return 'Chamando'
  if (callingState.value?.pacienteId === pacienteId) return String(callingState.value.secondsLeft)
  return 'Chamar'
}

const temPacienteEmAtendimento = computed(() => !!agendamentosStore.emAtendimento)

function nomePacienteChamada(ag: AgendamentoComPaciente) {
  return ag.paciente.nomeSocial || ag.paciente.nome
}

function mensagemErroChamada(error: unknown) {
  const fetchError = error as {
    data?: { statusMessage?: string, message?: string }
    statusMessage?: string
    message?: string
  }

  return fetchError.data?.statusMessage
    || fetchError.data?.message
    || fetchError.statusMessage
    || fetchError.message
    || 'Não foi possível chamar o paciente. Verifique a unidade ativa e tente novamente.'
}

async function chamarPaciente(ag: AgendamentoComPaciente) {
  if (!sala.value) {
    showSalaModal.value = true
    return
  }

  const clinicaId = ag.clinicaId ?? auth.activeClinicaId
  if (!clinicaId) {
    toast.add({
      title: 'Unidade não selecionada',
      description: 'Selecione uma unidade antes de chamar o paciente.',
      color: 'error',
      icon: 'i-lucide-alert-circle'
    })
    return
  }

  chamadaEmEnvio.value = ag.paciente.id

  try {
    await chamadosStore.chamarPaciente(ag.paciente.id, nomePacienteChamada(ag), sala.value, auth.user?.nome ?? 'Dr.', clinicaId)
  } catch (error) {
    toast.add({
      title: 'Erro ao chamar paciente',
      description: mensagemErroChamada(error),
      color: 'error',
      icon: 'i-lucide-alert-circle'
    })
    return
  } finally {
    chamadaEmEnvio.value = null
  }

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
    await agendamentosStore.atualizarStatus(ag.id, 'faltou', undefined, ag.clinicaId)
  } catch {
    console.error('Erro ao marcar falta')
  }
}

async function atenderAgendamento(ag: AgendamentoComPaciente) {
  try {
    await agendamentosStore.atualizarStatus(ag.id, 'em-atendimento', undefined, ag.clinicaId)
    await navigateTo('/atendimento-medico')
  } catch {
    console.error('Erro ao iniciar atendimento')
  }
}

async function editarAtendimento(ag: AgendamentoComPaciente) {
  try {
    await agendamentosStore.atualizarStatus(ag.id, 'em-atendimento', undefined, ag.clinicaId)
    await navigateTo(`/atendimento-medico?id=${ag.id}`)
  } catch {
    console.error('Erro ao reabrir atendimento')
  }
}

async function desfazerFalta(ag: AgendamentoComPaciente) {
  try {
    await agendamentosStore.atualizarStatus(ag.id, 'em-espera', undefined, ag.clinicaId)
  } catch {
    console.error('Erro ao desfazer falta')
  }
}

const modalConfirma = ref<{
  titulo: string
  descricao: string
  cor?: 'error' | 'success' | 'warning' | 'info' | 'neutral'
  onConfirm: () => void
} | null>(null)

function abrirModalFalta(ag: AgendamentoComPaciente) {
  const executar = () => faltouAgendamento(ag)
  modalConfirma.value = {
    titulo: 'Marcar como faltou?',
    descricao: `Tem certeza que deseja marcar "${ag.paciente.nome}" como faltou?`,
    cor: 'error',
    onConfirm: executar
  }
}

function abrirModalDesfazerFalta(ag: AgendamentoComPaciente) {
  const executar = () => desfazerFalta(ag)
  modalConfirma.value = {
    titulo: 'Desfazer falta?',
    descricao: `O paciente "${ag.paciente.nome}" voltará para a fila de espera.`,
    cor: 'warning',
    onConfirm: executar
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

const temPacientesDashboard = computed(() => totalPacientesDashboard.value > 0)

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
      <div
        v-if="!agendamentosStore.loading && temPacientesDashboard"
        class="grid grid-cols-1 md:grid-cols-2 gap-6"
      >
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
      <div
        v-else-if="agendamentosStore.loading"
        class="grid grid-cols-1 md:grid-cols-2 gap-6"
      >
        <UPageCard>
          <div class="flex flex-col gap-4 items-center justify-center h-full">
            <USkeleton class="h-40 w-40" />
            <USkeleton class="h-4 w-48" />
          </div>
        </UPageCard>
        <div class="grid grid-cols-2 gap-2 items-center">
          <UPageCard>
            <div class="flex flex-col gap-3 items-center">
              <USkeleton class="h-5 w-32" />
              <USkeleton class="h-8 w-20" />
            </div>
          </UPageCard>
          <UPageCard>
            <div class="flex flex-col gap-3 items-center">
              <USkeleton class="h-5 w-32" />
              <USkeleton class="h-8 w-20" />
            </div>
          </UPageCard>
          <UPageCard>
            <div class="flex flex-col gap-3 items-center">
              <USkeleton class="h-5 w-32" />
              <USkeleton class="h-8 w-20" />
            </div>
          </UPageCard>
          <UPageCard>
            <div class="flex flex-col gap-3 items-center">
              <USkeleton class="h-5 w-32" />
              <USkeleton class="h-8 w-20" />
            </div>
          </UPageCard>
        </div>
      </div>
      <div
        v-else
      >
        <UPageCard>
          <div class="flex flex-col gap-2 items-center">
            <div class="flex items-center gap-2 text-muted ">
              <p class="text-xl font-medium">
                Nenhum paciente na fila de espera nesse momento.
              </p>
            </div>
            <UIcon
              class="size-15"
              name="lucide:user-round-x"
            />
          </div>
        </UPageCard>
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

          <template #tipoProcedimento-cell="{ row }">
            <div class="min-w-40">
              <UBadge
                :label="rotuloTipo(row.original as AgendamentoComPaciente)"
                :color="corTipo(row.original.tipoProcedimento)"
                variant="subtle"
              />
              <p
                v-if="row.original.codigoProcedimentoSpdata"
                class="mt-1 text-xs text-muted"
              >
                TUSS {{ row.original.codigoProcedimentoSpdata }}
              </p>
            </div>
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
                :label="rotuloChamada(row.original.paciente.id)"
                size="sm"
                class="min-w-20"
                :color="isTerminal(row.original.status) ? 'neutral' : 'primary'"
                :variant="isTerminal(row.original.status) ? 'soft' : 'solid'"
                :loading="isChamadaBloqueada(row.original.paciente.id)"
                :disabled="temPacienteEmAtendimento || isTerminal(row.original.status) || isChamadaBloqueada(row.original.paciente.id)"
                @click="chamarPaciente(row.original as AgendamentoComPaciente)"
              />
              <UButton
                icon="i-lucide-user-x"
                label="Faltou"
                size="sm"
                :color="row.original.status === 'faltou' ? 'error' : (isTerminal(row.original.status) ? 'neutral' : 'error')"
                :variant="isTerminal(row.original.status) ? 'soft' : 'solid'"
                :disabled="temPacienteEmAtendimento || isTerminal(row.original.status) || isChamadaBloqueada(row.original.paciente.id)"
                @click="abrirModalFalta(row.original as AgendamentoComPaciente)"
              />
              <UButton
                :icon="row.original.status === 'atendido' ? 'i-lucide-check-circle' : 'i-lucide-user-check'"
                :label="statusLabel(row.original.status)"
                size="sm"
                :color="statusColor(row.original.status)"
                :variant="atendimentoVariant(row.original.status)"
                :disabled="temPacienteEmAtendimento || atendimentoDisabled(row.original.status) || isChamadaBloqueada(row.original.paciente.id)"
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
          :columns="colunas"
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

          <template #tipoProcedimento-cell="{ row }">
            <div class="min-w-40">
              <UBadge
                :label="rotuloTipo(row.original as AgendamentoComPaciente)"
                :color="corTipo(row.original.tipoProcedimento)"
                variant="subtle"
              />
              <p
                v-if="row.original.codigoProcedimentoSpdata"
                class="mt-1 text-xs text-muted"
              >
                TUSS {{ row.original.codigoProcedimentoSpdata }}
              </p>
            </div>
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
                v-if="row.original.status === 'atendido'"
                icon="i-lucide-pencil"
                label="Editar atendimento"
                size="sm"
                color="primary"
                @click="editarAtendimento(row.original as AgendamentoComPaciente)"
              />
              <UButton
                v-else-if="row.original.status === 'faltou'"
                icon="i-lucide-undo-2"
                label="Desfazer falta"
                size="sm"
                color="neutral"
                @click="abrirModalDesfazerFalta(row.original as AgendamentoComPaciente)"
              />
            </div>
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
    <ModalConfirmacao
      :abrir="!!modalConfirma"
      :titulo="modalConfirma?.titulo ?? ''"
      :descricao="modalConfirma?.descricao ?? ''"
      :cor-confirma="modalConfirma?.cor ?? 'error'"
      texto-confirma="Confirmar"
      @fechar="modalConfirma = null"
      @confirmar="modalConfirma?.onConfirm(); modalConfirma = null"
    />
  </div>
</template>
