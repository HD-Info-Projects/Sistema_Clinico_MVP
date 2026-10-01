<script setup lang="ts">
import {
  iniciarSpdataSync,
  listarSpdataSync
} from '~/features/spdata-sync/services/spdataSyncService'
import type {
  SpdataSyncCounters,
  SpdataSyncJob,
  SpdataSyncStatus,
  SpdataSyncTarget
} from '~/features/spdata-sync/types'

definePageMeta({ layout: 'admin' })

const openNav = inject<() => void>('openNav', () => {})
const toast = useToast()
const jobs = ref<SpdataSyncJob[]>([])
const activeJob = ref<SpdataSyncJob | null>(null)
const loading = ref(true)
const submitting = ref(false)
const errorMessage = ref('')
const offset = ref(0)
const limit = 10
const hasMore = ref(false)
const confirmTarget = ref<SpdataSyncTarget | null>(null)
let pollTimer: ReturnType<typeof setTimeout> | null = null
let notifiedJobId: number | null = null

const activeStatuses = new Set<SpdataSyncStatus>(['QUEUED', 'RUNNING', 'RETRYING'])

const targetLabels: Record<SpdataSyncTarget, string> = {
  TODOS: 'Exames e procedimentos',
  EXAMES: 'Exames',
  PROCEDIMENTOS: 'Procedimentos'
}

const statusLabels: Record<SpdataSyncStatus, string> = {
  QUEUED: 'Aguardando',
  RUNNING: 'Executando',
  RETRYING: 'Tentando novamente',
  SUCCEEDED: 'Concluída',
  SUCCEEDED_WITH_ERRORS: 'Concluída com erros',
  FAILED: 'Falhou'
}

function statusColor(status: SpdataSyncStatus): 'neutral' | 'info' | 'warning' | 'success' | 'error' {
  if (status === 'SUCCEEDED') return 'success'
  if (status === 'SUCCEEDED_WITH_ERRORS' || status === 'RETRYING') return 'warning'
  if (status === 'FAILED') return 'error'
  if (status === 'RUNNING') return 'info'
  return 'neutral'
}

function formatDate(value: string | null) {
  if (!value) return '-'
  return new Intl.DateTimeFormat('pt-BR', {
    dateStyle: 'short',
    timeStyle: 'medium'
  }).format(new Date(value))
}

function duration(job: SpdataSyncJob) {
  if (!job.started_at) return '-'
  const end = job.finished_at ? new Date(job.finished_at).getTime() : Date.now()
  const seconds = Math.max(0, Math.round((end - new Date(job.started_at).getTime()) / 1000))
  if (seconds < 60) return `${seconds}s`
  const minutes = Math.floor(seconds / 60)
  return `${minutes}min ${seconds % 60}s`
}

function counters(job: SpdataSyncJob, key: 'exames' | 'procedimentos'): SpdataSyncCounters | null {
  return job.result?.[key] || job.progress?.[key] || null
}

function extractError(error: unknown) {
  const typed = error as {
    data?: { error?: string, message?: string }
    statusMessage?: string
    message?: string
  }
  return typed.data?.error || typed.data?.message || typed.statusMessage || typed.message || 'Erro inesperado.'
}

function stopPolling() {
  if (pollTimer) clearTimeout(pollTimer)
  pollTimer = null
}

function schedulePolling() {
  stopPolling()
  if (!activeJob.value) return
  pollTimer = setTimeout(() => void loadJobs(false), 2500)
}

function notifyFinished(job: SpdataSyncJob) {
  if (notifiedJobId === job.id) return
  notifiedJobId = job.id
  if (job.status === 'SUCCEEDED') {
    toast.add({ title: 'Sincronização concluída', color: 'success' })
  } else if (job.status === 'SUCCEEDED_WITH_ERRORS') {
    toast.add({ title: 'Sincronização concluída com registros ignorados', color: 'warning' })
  } else if (job.status === 'FAILED') {
    toast.add({ title: job.error_message || 'A sincronização falhou', color: 'error' })
  }
}

async function loadJobs(showLoading = true) {
  if (showLoading) loading.value = true
  errorMessage.value = ''
  const previousActive = activeJob.value
  try {
    const response = await listarSpdataSync(limit, offset.value)
    jobs.value = response.items
    activeJob.value = response.active_job
    hasMore.value = response.has_more

    if (previousActive && !response.active_job) {
      const finished = response.items.find(job => job.id === previousActive.id)
      if (finished && !activeStatuses.has(finished.status)) notifyFinished(finished)
    }
  } catch (error) {
    errorMessage.value = extractError(error)
  } finally {
    loading.value = false
    if (activeJob.value) schedulePolling()
    else stopPolling()
  }
}

function askConfirmation(target: SpdataSyncTarget) {
  confirmTarget.value = target
}

async function startSync() {
  if (!confirmTarget.value || submitting.value) return
  const target = confirmTarget.value
  confirmTarget.value = null
  submitting.value = true
  try {
    const response = await iniciarSpdataSync(target)
    activeJob.value = response.job
    offset.value = 0
    toast.add({ title: response.message, color: 'success' })
    await loadJobs(false)
  } catch (error) {
    toast.add({ title: extractError(error), color: 'error' })
    await loadJobs(false)
  } finally {
    submitting.value = false
  }
}

async function previousPage() {
  offset.value = Math.max(0, offset.value - limit)
  await loadJobs()
}

async function nextPage() {
  offset.value += limit
  await loadJobs()
}

onMounted(() => void loadJobs())
onUnmounted(stopPolling)
</script>

<template>
  <div>
    <UHeader
      title="Sincronização SPDATA"
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
      <template #right>
        <UColorModeButton />
      </template>
    </UHeader>

    <main class="min-h-screen space-y-6 bg-muted p-4 sm:p-6">
      <UAlert
        title="Importação dos catálogos do SPDATA"
        description="A sincronização cria registros novos e atualiza os existentes. Registros removidos na origem não são excluídos localmente."
        icon="i-lucide-database"
        color="info"
        variant="subtle"
      />

      <section class="grid gap-4 lg:grid-cols-3">
        <UCard class="lg:col-span-2">
          <template #header>
            <div class="flex items-center gap-3">
              <div class="rounded-xl bg-primary/10 p-3 text-primary">
                <UIcon
                  name="i-lucide-refresh-cw"
                  class="size-6"
                />
              </div>
              <div>
                <h2 class="text-lg font-bold">
                  Atualizar catálogos
                </h2>
                <p class="text-sm text-muted">
                  O processamento acontece em segundo plano, em lotes de 200 registros.
                </p>
              </div>
            </div>
          </template>

          <div class="grid gap-3 sm:grid-cols-3">
            <UButton
              label="Sincronizar tudo"
              icon="i-lucide-database-zap"
              size="lg"
              block
              :loading="submitting"
              :disabled="Boolean(activeJob)"
              @click="askConfirmation('TODOS')"
            />
            <UButton
              label="Somente exames"
              icon="i-lucide-flask-conical"
              color="neutral"
              variant="outline"
              size="lg"
              block
              :disabled="Boolean(activeJob) || submitting"
              @click="askConfirmation('EXAMES')"
            />
            <UButton
              label="Somente procedimentos"
              icon="i-lucide-clipboard-list"
              color="neutral"
              variant="outline"
              size="lg"
              block
              :disabled="Boolean(activeJob) || submitting"
              @click="askConfirmation('PROCEDIMENTOS')"
            />
          </div>
        </UCard>

        <UCard>
          <template #header>
            <h2 class="font-bold">
              Estado atual
            </h2>
          </template>
          <div
            v-if="activeJob"
            class="space-y-3"
          >
            <div class="flex items-center justify-between gap-3">
              <UBadge
                :label="statusLabels[activeJob.status]"
                :color="statusColor(activeJob.status)"
                variant="subtle"
              />
              <span class="font-mono text-xs text-muted">#{{ activeJob.id }}</span>
            </div>
            <p class="font-medium">
              {{ targetLabels[activeJob.target] }}
            </p>
            <p class="text-sm text-muted">
              {{ activeJob.current_stage ? `Processando ${activeJob.current_stage.toLowerCase()}` : 'Aguardando o worker' }}
            </p>
            <div class="h-1.5 overflow-hidden rounded-full bg-default">
              <div class="h-full w-1/3 animate-pulse rounded-full bg-primary" />
            </div>
          </div>
          <div
            v-else
            class="py-4 text-center text-sm text-muted"
          >
            Nenhuma sincronização em andamento.
          </div>
        </UCard>
      </section>

      <UAlert
        v-if="errorMessage"
        :title="errorMessage"
        color="error"
        icon="i-lucide-circle-alert"
        variant="subtle"
      />

      <section>
        <div class="mb-3 flex items-center justify-between gap-3">
          <div>
            <h2 class="text-xl font-bold">
              Histórico
            </h2>
            <p class="text-sm text-muted">
              Execuções realizadas pelo painel e pelo terminal.
            </p>
          </div>
          <UButton
            icon="i-lucide-refresh-cw"
            color="neutral"
            variant="ghost"
            aria-label="Atualizar histórico"
            :loading="loading"
            @click="loadJobs()"
          />
        </div>

        <div
          v-if="loading && jobs.length === 0"
          class="flex justify-center py-16"
        >
          <UIcon
            name="i-lucide-loader-circle"
            class="size-8 animate-spin text-muted"
          />
        </div>

        <UCard v-else-if="jobs.length === 0">
          <div class="py-10 text-center text-muted">
            Nenhuma sincronização registrada.
          </div>
        </UCard>

        <div
          v-else
          class="space-y-3"
        >
          <UCard
            v-for="job in jobs"
            :key="job.id"
          >
            <div class="grid gap-4 lg:grid-cols-12 lg:items-center">
              <div class="lg:col-span-3">
                <div class="mb-1 flex items-center gap-2">
                  <UBadge
                    :label="statusLabels[job.status]"
                    :color="statusColor(job.status)"
                    variant="subtle"
                  />
                  <span class="font-mono text-xs text-muted">#{{ job.id }}</span>
                </div>
                <p class="font-semibold">
                  {{ targetLabels[job.target] }}
                </p>
                <p class="text-xs text-muted">
                  {{ job.origin === 'CLI' ? 'Terminal' : (job.requested_by?.nome_completo || 'Administrador') }}
                </p>
              </div>

              <div class="grid grid-cols-2 gap-3 lg:col-span-4">
                <div>
                  <p class="text-xs font-semibold uppercase tracking-wide text-muted">
                    Exames
                  </p>
                  <p class="text-sm">
                    {{ counters(job, 'exames')?.lidos ?? 0 }} lidos
                  </p>
                  <p class="text-xs text-muted">
                    {{ counters(job, 'exames')?.criados ?? 0 }} novos · {{ counters(job, 'exames')?.erros ?? 0 }} erros
                  </p>
                </div>
                <div>
                  <p class="text-xs font-semibold uppercase tracking-wide text-muted">
                    Procedimentos
                  </p>
                  <p class="text-sm">
                    {{ counters(job, 'procedimentos')?.lidos ?? 0 }} lidos
                  </p>
                  <p class="text-xs text-muted">
                    {{ counters(job, 'procedimentos')?.criados ?? 0 }} novos · {{ counters(job, 'procedimentos')?.erros ?? 0 }} erros
                  </p>
                </div>
              </div>

              <div class="lg:col-span-3">
                <p class="text-sm">
                  {{ formatDate(job.started_at || job.queued_at) }}
                </p>
                <p class="text-xs text-muted">
                  Duração: {{ duration(job) }} · Tentativa {{ job.attempts }}/{{ job.max_attempts }}
                </p>
              </div>

              <div class="lg:col-span-2">
                <p
                  v-if="job.error_message"
                  class="text-sm text-error"
                >
                  {{ job.error_message }}
                </p>
                <p
                  v-else
                  class="text-sm text-muted"
                >
                  {{ job.finished_at ? `Finalizada em ${formatDate(job.finished_at)}` : 'Em andamento' }}
                </p>
              </div>
            </div>
          </UCard>

          <div class="flex justify-end gap-2">
            <UButton
              label="Anterior"
              color="neutral"
              variant="outline"
              :disabled="offset === 0"
              @click="previousPage"
            />
            <UButton
              label="Próxima"
              color="neutral"
              variant="outline"
              :disabled="!hasMore"
              @click="nextPage"
            />
          </div>
        </div>
      </section>
    </main>

    <ModalConfirmacao
      :abrir="confirmTarget !== null"
      titulo="Iniciar sincronização?"
      :descricao="`O sistema importará ${confirmTarget ? targetLabels[confirmTarget].toLowerCase() : ''} do SPDATA. A operação continuará em segundo plano mesmo se você sair desta página.`"
      texto-confirma="Iniciar"
      cor-confirma="success"
      icone="i-lucide-refresh-cw"
      @fechar="confirmTarget = null"
      @confirmar="startSync"
    />
  </div>
</template>
