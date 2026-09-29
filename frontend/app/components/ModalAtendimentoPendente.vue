<script setup lang="ts">
import type { AgendamentoComPaciente } from '~/features/agenda/types'
import { atualizarStatusAgendamento } from '~/features/agenda/services/agendaService'

// Pergunta ao médico o que fazer com atendimentos que ficaram "em atendimento"
// em dias anteriores: retomar, finalizar (salvar) ou cancelar. Mostra um por vez.
const pendentes = defineModel<AgendamentoComPaciente[]>('pendentes', { default: () => [] })

const emit = defineEmits<{
  retomar: [agendamento: AgendamentoComPaciente]
}>()

const toast = useToast()

const atual = computed(() => pendentes.value[0] ?? null)
const etapa = ref<'escolha' | 'confirmar-cancelamento'>('escolha')
const processando = ref<'salvar' | 'cancelar' | null>(null)

const modalEscolhaAberto = computed(() => !!atual.value && etapa.value === 'escolha')
const modalCancelarAberto = computed(() => !!atual.value && etapa.value === 'confirmar-cancelamento')

const consultaDoRascunho = computed(() =>
  atual.value ? lerConsultaDoDraft(atual.value.id, atual.value.paciente.id) : null
)

function formatarData(data?: string | null) {
  if (!data) return '—'
  const [ano, mes, dia] = data.slice(0, 10).split('-')
  return ano && mes && dia ? `${dia}/${mes}/${ano}` : data
}

function concluirAtual() {
  const ag = atual.value
  if (ag) removerDraftAtendimento(ag.id, ag.paciente.id)
  pendentes.value = pendentes.value.slice(1)
  etapa.value = 'escolha'
}

function retomar() {
  if (!atual.value || processando.value) return
  emit('retomar', atual.value)
}

async function salvar() {
  const ag = atual.value
  if (!ag || processando.value) return

  processando.value = 'salvar'
  try {
    await atualizarStatusAgendamento(ag.id, 'atendido', consultaDoRascunho.value ?? undefined, ag.clinicaId)
    toast.add({
      title: 'Atendimento finalizado',
      description: `O atendimento de ${ag.paciente.nome} foi finalizado.`,
      color: 'success',
      icon: 'i-lucide-check-circle'
    })
    concluirAtual()
  } catch {
    toast.add({
      title: 'Erro ao finalizar atendimento',
      description: 'Não foi possível finalizar o atendimento. Tente novamente.',
      color: 'error',
      icon: 'i-lucide-alert-circle'
    })
  } finally {
    processando.value = null
  }
}

async function cancelarDefinitivamente() {
  const ag = atual.value
  if (!ag || processando.value) return

  processando.value = 'cancelar'
  try {
    await atualizarStatusAgendamento(ag.id, 'cancelado', undefined, ag.clinicaId)
    toast.add({
      title: 'Atendimento cancelado',
      description: `O atendimento de ${ag.paciente.nome} foi cancelado.`,
      color: 'neutral',
      icon: 'i-lucide-x-circle'
    })
    concluirAtual()
  } catch {
    toast.add({
      title: 'Erro ao cancelar atendimento',
      description: 'Não foi possível cancelar o atendimento. Tente novamente.',
      color: 'error',
      icon: 'i-lucide-alert-circle'
    })
    etapa.value = 'escolha'
  } finally {
    processando.value = null
  }
}
</script>

<template>
  <UModal
    :open="modalEscolhaAberto"
    :close="false"
    :dismissible="false"
    :ui="{ content: 'max-h-[calc(100dvh-2rem)] overflow-y-auto' }"
  >
    <template #content>
      <div
        v-if="atual"
        class="space-y-4 p-4 sm:p-6"
      >
        <div class="flex min-w-0 items-start gap-2">
          <UIcon
            name="i-lucide-alert-triangle"
            class="mt-1 shrink-0 text-warning"
          />
          <h3 class="min-w-0 break-words text-xl font-black">
            Atendimento não finalizado
          </h3>
        </div>

        <p class="break-words text-neutral-500 dark:text-neutral-400">
          O atendimento de
          <span class="font-semibold text-highlighted">{{ atual.paciente.nome }}</span>,
          de {{ formatarData(atual.data) }}{{ atual.horario ? ` às ${atual.horario}` : '' }},
          ficou em andamento e não foi finalizado. O que deseja fazer?
        </p>

        <UAlert
          v-if="consultaDoRascunho"
          color="success"
          variant="subtle"
          icon="i-lucide-save"
          description="Há um rascunho salvo neste navegador. Ao salvar, o conteúdo dele será registrado."
        />
        <UAlert
          v-else
          color="neutral"
          variant="subtle"
          icon="i-lucide-info"
          description="Nenhum rascunho foi encontrado. Ao salvar, o atendimento será finalizado sem anamnese, diagnóstico ou prescrição. Para registrar o conteúdo, retome o atendimento."
        />

        <p
          v-if="pendentes.length > 1"
          class="text-sm text-muted"
        >
          Há mais {{ pendentes.length - 1 }} atendimento<span v-if="pendentes.length > 2">s</span> pendente<span v-if="pendentes.length > 2">s</span>.
        </p>

        <div class="grid grid-cols-1 gap-3 sm:grid-cols-3">
          <UButton
            label="Cancelar atendimento"
            icon="i-lucide-x-circle"
            color="error"
            variant="soft"
            block
            size="lg"
            class="font-bold rounded-xl"
            :disabled="!!processando"
            @click="etapa = 'confirmar-cancelamento'"
          />
          <UButton
            label="Salvar"
            icon="i-lucide-check-circle"
            color="success"
            variant="soft"
            block
            size="lg"
            class="font-bold rounded-xl"
            :loading="processando === 'salvar'"
            :disabled="!!processando"
            @click="void salvar()"
          />
          <UButton
            label="Retomar"
            icon="i-lucide-stethoscope"
            color="primary"
            variant="solid"
            block
            size="lg"
            class="font-bold rounded-xl"
            :disabled="!!processando"
            @click="retomar()"
          />
        </div>
      </div>
    </template>
  </UModal>

  <UModal
    :open="modalCancelarAberto"
    :close="false"
    :dismissible="false"
    :ui="{ content: 'max-h-[calc(100dvh-2rem)] overflow-y-auto' }"
  >
    <template #content>
      <div class="space-y-4 p-4 sm:p-6">
        <div class="flex min-w-0 items-start gap-2">
          <UIcon
            name="i-lucide-trash-2"
            class="mt-1 shrink-0 text-error"
          />
          <h3 class="min-w-0 break-words text-xl font-black">
            Cancelar atendimento?
          </h3>
        </div>
        <p class="break-words text-neutral-500 dark:text-neutral-400">
          Todas as alterações feitas neste atendimento serão descartadas e
          <span class="font-semibold text-error">não há como desfazer</span>.
          O paciente voltará para a fila.
        </p>
        <div class="grid grid-cols-1 gap-3 sm:grid-cols-2">
          <UButton
            label="Voltar"
            color="neutral"
            variant="ghost"
            block
            size="lg"
            class="font-bold rounded-xl"
            :disabled="!!processando"
            @click="etapa = 'escolha'"
          />
          <UButton
            label="Cancelar definitivamente"
            color="error"
            variant="solid"
            block
            size="lg"
            class="font-bold rounded-xl"
            :loading="processando === 'cancelar'"
            :disabled="!!processando"
            @click="void cancelarDefinitivamente()"
          />
        </div>
      </div>
    </template>
  </UModal>
</template>
