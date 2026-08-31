<script setup lang="ts">
import type { Clinica } from '~/types'
import { useSse } from '~/composables/useSse'

const route = useRoute()
const chamadosStore = useChamadosStore()

const unidade = ref<Clinica | null>(null)
const painelError = ref('')

const clinicaId = computed(() => {
  const raw = Array.isArray(route.params.id) ? route.params.id[0] : route.params.id
  const id = Number(raw)
  return Number.isInteger(id) && id > 0 ? id : null
})

const audioRef = ref<HTMLAudioElement | null>(null)
const audioUrl = ref<string | null>(null)
const audioAtivo = ref(false)
const audioBloqueado = ref(false)
const audioAtivando = ref(false)
const ttsLoading = ref(false)
const ttsError = ref(false)
const ttsErrorMensagem = ref('')
const ttsRequestId = ref(0)
const ttsAbortController = ref<AbortController | null>(null)

function revogarObjectUrl(url: string) {
  window.setTimeout(() => URL.revokeObjectURL(url), 0)
}

function criarAudioSilenciosoUrl() {
  const sampleRate = 8000
  const sampleCount = sampleRate / 20
  const dataSize = sampleCount * 2
  const buffer = new ArrayBuffer(44 + dataSize)
  const view = new DataView(buffer)

  function writeString(offset: number, value: string) {
    for (let i = 0; i < value.length; i++) {
      view.setUint8(offset + i, value.charCodeAt(i))
    }
  }

  writeString(0, 'RIFF')
  view.setUint32(4, 36 + dataSize, true)
  writeString(8, 'WAVE')
  writeString(12, 'fmt ')
  view.setUint32(16, 16, true)
  view.setUint16(20, 1, true)
  view.setUint16(22, 1, true)
  view.setUint32(24, sampleRate, true)
  view.setUint32(28, sampleRate * 2, true)
  view.setUint16(32, 2, true)
  view.setUint16(34, 16, true)
  writeString(36, 'data')
  view.setUint32(40, dataSize, true)

  return URL.createObjectURL(new Blob([buffer], { type: 'audio/wav' }))
}

async function testarAudioPermitido() {
  const url = criarAudioSilenciosoUrl()
  const audio = new Audio(url)

  try {
    await audio.play()
    return true
  } catch {
    return false
  } finally {
    audio.pause()
    audio.removeAttribute('src')
    audio.load()
    revogarObjectUrl(url)
  }
}

function limparAudioAtual() {
  if (audioRef.value) {
    audioRef.value.pause()
    audioRef.value.removeAttribute('src')
    audioRef.value.load()
  }
  audioRef.value = null

  if (audioUrl.value) {
    revogarObjectUrl(audioUrl.value)
    audioUrl.value = null
  }
}

async function ativarAudio() {
  if (audioAtivando.value || audioAtivo.value) return

  audioAtivando.value = true
  ttsError.value = false
  ttsErrorMensagem.value = ''
  audioBloqueado.value = false

  const permitido = await testarAudioPermitido()
  audioAtivo.value = permitido
  audioBloqueado.value = !permitido
  audioAtivando.value = false
}

function ativarAudioPorInteracao() {
  if (audioAtivo.value || audioAtivando.value) return
  void ativarAudio()
}

async function falarChamado(chamadoId: number) {
  if (!audioAtivo.value) return

  const requestId = ttsRequestId.value + 1
  ttsRequestId.value = requestId
  ttsAbortController.value?.abort()

  const abortController = new AbortController()
  ttsAbortController.value = abortController

  limparAudioAtual()
  ttsLoading.value = true
  ttsError.value = false
  ttsErrorMensagem.value = ''

  try {
    const res = await fetch('/api/tts/speak', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ chamadoId }),
      signal: abortController.signal
    })

    if (!res.ok) {
      let message = 'Erro ao gerar áudio'

      try {
        const body = await res.json() as { statusMessage?: string, message?: string }
        message = body.statusMessage || body.message || message
      } catch {
        // Mantém a mensagem padrão quando a resposta não é JSON.
      }

      throw new Error(message)
    }
    if (requestId !== ttsRequestId.value) return

    const blob = await res.blob()
    if (requestId !== ttsRequestId.value) return

    const url = URL.createObjectURL(blob)
    const audio = new Audio(url)

    audioUrl.value = url
    audioRef.value = audio

    audio.onended = () => {
      if (requestId !== ttsRequestId.value) return
      ttsLoading.value = false
      limparAudioAtual()
    }
    audio.onerror = () => {
      if (requestId !== ttsRequestId.value) return
      ttsLoading.value = false
      ttsError.value = true
      limparAudioAtual()
    }

    await audio.play()
  } catch (error) {
    if (error instanceof DOMException && error.name === 'AbortError') return
    if (requestId !== ttsRequestId.value) return

    if (error instanceof DOMException && error.name === 'NotAllowedError') {
      audioAtivo.value = false
      audioBloqueado.value = true
      ttsLoading.value = false
      ttsError.value = false
      ttsErrorMensagem.value = ''
      limparAudioAtual()
      return
    }

    ttsLoading.value = false
    ttsError.value = true
    ttsErrorMensagem.value = error instanceof Error ? error.message : 'Erro ao gerar áudio'
    limparAudioAtual()
  }
}

onMounted(async () => {
  if (!clinicaId.value) {
    painelError.value = 'Unidade inválida'
    return
  }

  try {
    unidade.value = await $fetch<Clinica>(`/api/clinicas/${clinicaId.value}`)
  } catch (error) {
    console.error('Erro ao carregar unidade do painel de chamada', error)
  }

  await ativarAudio()

  chamadosStore.init({ public: true, clinicaId: clinicaId.value })

  const sse = useSse()
  sse.on('chamado:novo', (data: unknown) => {
    const chamado = data as { id?: number, pacienteNome?: string }
    if (chamado?.id && chamado.pacienteNome) {
      void falarChamado(chamado.id)
    }
  })
  sse.connect({ public: true, clinicaId: clinicaId.value })
})

onBeforeUnmount(() => {
  ttsRequestId.value += 1
  ttsAbortController.value?.abort()
  limparAudioAtual()
})

const { horaFormatada, dataFormatada } = useRelogio()

const unidadeLabel = computed(() => unidade.value?.nome || (clinicaId.value ? `Unidade #${clinicaId.value}` : 'Unidade'))
const ultimoChamado = computed(() => chamadosStore.ultimoChamado)
const ultimasChamadas = computed(() => chamadosStore.historicoChamados.slice(0, 4))
const mostrarDesbloqueioAudio = computed(() => !audioAtivo.value && !painelError.value)
const mensagemAudio = computed(() => audioBloqueado.value
  ? 'Áudio bloqueado pelo navegador'
  : 'Tentando ativar áudio automaticamente')
</script>

<template>
  <div
    class="relative flex h-dvh flex-col gap-3 overflow-y-auto p-3 sm:gap-4 sm:p-6 lg:overflow-hidden"
    tabindex="0"
    aria-label="Painel de chamada. Pressione Enter ou Espaço para ativar o áudio."
    @pointerdown="ativarAudioPorInteracao"
    @keydown.space.prevent="ativarAudioPorInteracao"
    @keydown.enter.prevent="ativarAudioPorInteracao"
  >
    <div
      v-if="painelError"
      class="flex h-full items-center justify-center"
    >
      <UAlert
        :title="painelError"
        description="Verifique o endereço do painel de chamada da unidade."
        color="error"
        variant="subtle"
        icon="i-lucide-circle-alert"
        class="max-w-lg"
      />
    </div>

    <template v-else>
      <header class="flex shrink-0 flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div class="flex min-w-0 flex-wrap items-center gap-2 sm:gap-3">
          <LogoMed :tipo="0" />
          <UBadge
            :label="unidadeLabel"
            color="primary"
            variant="soft"
            size="lg"
            class="max-w-full"
            :ui="{ label: 'truncate' }"
          />
          <UButton
            v-if="!audioAtivo"
            icon="i-lucide-volume-2"
            :label="audioBloqueado ? 'Ativar áudio' : 'Ativando áudio'"
            color="primary"
            variant="soft"
            :loading="audioAtivando"
            :aria-label="audioBloqueado ? 'Ativar áudio das chamadas' : 'Áudio sendo ativado'"
            @click.stop="ativarAudioPorInteracao"
          />
          <div
            v-else-if="ttsLoading"
            class="flex items-center gap-1 text-sm text-muted"
            role="status"
            aria-live="polite"
          >
            <UIcon
              name="i-lucide-volume-2"
              class="animate-pulse"
            />
            Falando...
          </div>
          <div
            v-else-if="ttsError"
            class="flex items-center gap-1 text-sm text-error"
            role="alert"
          >
            <UIcon name="i-lucide-volume-x" />
            {{ ttsErrorMensagem || 'Erro no áudio' }}
          </div>
          <UBadge
            v-else
            icon="i-lucide-volume-2"
            color="success"
            variant="soft"
          />
        </div>
        <div class="shrink-0 text-left sm:text-right">
          <p class="text-[clamp(1rem,2.5vw,1.5rem)] font-light text-muted">
            {{ dataFormatada }}
          </p>
          <p class="text-[clamp(2rem,5vw,3rem)] font-bold tracking-tight text-foreground tabular-nums">
            {{ horaFormatada }}
          </p>
        </div>
      </header>

      <main class="flex flex-1 flex-col gap-3 lg:min-h-0 lg:flex-row lg:gap-4">
        <div class="flex min-h-96 min-w-0 flex-2 flex-col gap-4 lg:min-h-0">
          <template v-if="ultimoChamado">
            <UCard
              class="flex flex-1 flex-col items-center justify-center bg-primary-600 p-4 sm:p-6 lg:p-10 dark:bg-primary-700/80"
              role="status"
              aria-live="assertive"
              aria-atomic="true"
            >
              <div class="w-full">
                <p class="mb-3 text-center text-[clamp(0.875rem,2vw,1.25rem)] font-medium uppercase tracking-widest text-white sm:mb-4">
                  Chamando Agora
                </p>

                <p class="mb-4 break-words text-center text-[clamp(2rem,6vw,4.5rem)] font-bold leading-tight text-white [overflow-wrap:anywhere] sm:mb-6">
                  {{ ultimoChamado.pacienteNome }}
                </p>
              </div>

              <div class="mb-6 flex w-full flex-col items-center justify-center gap-4">
                <UPageCard
                  class="w-full flex-1 bg-white/20 p-2! text-center"
                  variant="subtle"
                  :ui="{ container: 'p-0 sm:p-0' }"
                >
                  <p class="text-[clamp(0.75rem,1.8vw,1.125rem)] uppercase tracking-wider text-white">
                    Local de Atendimento
                  </p>
                  <p class="break-words text-[clamp(1.5rem,4vw,2.25rem)] font-semibold text-white [overflow-wrap:anywhere]">
                    {{ ultimoChamado.localAtendimento }}
                  </p>
                </UPageCard>
                <UPageCard
                  class="w-full flex-1 bg-white/20 p-2! text-center"
                  variant="subtle"
                  :ui="{ container: 'p-0 sm:p-0' }"
                >
                  <p class="text-[clamp(0.75rem,1.8vw,1.125rem)] uppercase tracking-wider text-white">
                    Médico Responsável
                  </p>
                  <p class="break-words text-[clamp(1.5rem,4vw,2.25rem)] font-semibold text-white [overflow-wrap:anywhere]">
                    {{ ultimoChamado.medicoResponsavel || 'Atendimento' }}
                  </p>
                </UPageCard>
              </div>

              <div class="flex items-center justify-center gap-3">
                <UIcon
                  name="i-lucide-arrow-right"
                  class="animate-pulse text-white"
                />
                <p class="animate-pulse text-center text-[clamp(1rem,3vw,1.875rem)] font-medium text-white">
                  Por favor, dirija-se à sala indicada.
                </p>
              </div>
            </UCard>
          </template>

          <template v-else>
            <UCard class="flex flex-1 flex-col items-center justify-center bg-primary-600 p-4 text-center sm:p-6 lg:p-10 dark:bg-primary-700/80">
              <UIcon
                name="i-lucide-stethoscope"
                class="text-7xl text-white"
              />
              <p class="mt-4 text-[clamp(1.25rem,3vw,1.5rem)] font-medium text-white">
                Nenhuma chamada no momento
              </p>
              <p class="mt-1 text-base text-white">
                A lista de chamadas aparecerá aqui automaticamente.
              </p>
            </UCard>
          </template>
        </div>

        <UCard
          class="flex min-h-80 min-w-0 flex-1 flex-col overflow-hidden lg:min-h-0"
          :ui="{ body: 'p-0 md:p-0 lg:p-0' }"
        >
          <template #title>
            <div class="flex items-start gap-3">
              <UIcon
                name="i-lucide-list-check"
                class="shrink-0 text-2xl text-primary"
              />
              <p class="break-words text-base font-bold uppercase tracking-widest text-primary sm:text-lg">
                Últimas Chamadas
              </p>
            </div>
          </template>

          <div
            v-if="ultimasChamadas.length"
            class="flex min-h-0 flex-1 flex-col gap-2 overflow-y-auto p-2"
          >
            <UCard
              v-for="chamado in ultimasChamadas"
              :key="chamado.id"
            >
              <p class="line-clamp-2 break-words text-xl font-semibold text-foreground [overflow-wrap:anywhere] sm:text-2xl">
                {{ chamado.pacienteNome }}
              </p>
              <div class="mt-1 flex flex-wrap items-center justify-between gap-2 text-sm text-muted">
                <UBadge
                  :label="chamado.localAtendimento"
                  color="primary"
                  variant="soft"
                  size="lg"
                  class="max-w-full"
                  :ui="{ label: 'truncate' }"
                />
                <span>{{ chamado.dataChamada }}</span>
              </div>
            </UCard>
          </div>

          <div
            v-else
            class="flex flex-1 items-center justify-center"
          >
            <p class="text-base text-muted">
              Nenhuma chamada realizada
            </p>
          </div>
        </UCard>
      </main>

      <div
        v-if="mostrarDesbloqueioAudio"
        class="absolute inset-0 z-20 flex items-center justify-center bg-neutral-950/65 p-6 backdrop-blur-sm"
        role="dialog"
        aria-modal="true"
        aria-labelledby="titulo-ativar-audio"
        aria-describedby="descricao-ativar-audio"
      >
        <UCard
          class="w-full max-w-xl text-center shadow-2xl"
          :ui="{ body: 'p-8 sm:p-10' }"
        >
          <div class="mx-auto mb-5 flex size-20 items-center justify-center rounded-full bg-primary/10">
            <UIcon
              name="i-lucide-volume-2"
              class="text-5xl text-primary"
            />
          </div>
          <p
            id="titulo-ativar-audio"
            class="mb-2 text-[clamp(1.5rem,5vw,1.875rem)] font-bold text-foreground"
          >
            Iniciar painel com áudio
          </p>
          <p
            id="descricao-ativar-audio"
            class="mb-6 text-base text-muted sm:text-lg"
          >
            {{ mensagemAudio }}. Toque ou clique uma vez para liberar as chamadas sonoras nesta tela.
          </p>
          <UButton
            icon="i-lucide-volume-2"
            label="Iniciar áudio"
            color="primary"
            size="xl"
            class="justify-center"
            :loading="audioAtivando"
            @click.stop="ativarAudioPorInteracao"
          />
        </UCard>
      </div>
    </template>
  </div>
</template>
