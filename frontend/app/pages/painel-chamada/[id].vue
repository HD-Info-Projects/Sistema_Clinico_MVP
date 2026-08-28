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
  limparTimerChamado()
})

const { horaFormatada, dataFormatada } = useRelogio()

const videosPlaylist = ['/media/1.mp4', '/media/2.mp4', '/media/3.mp4', '/media/4.mp4']

const videoIndexAtual = ref(0)
const videoRef = ref<HTMLVideoElement | null>(null)

function avancarVideo() {
  videoIndexAtual.value = (videoIndexAtual.value + 1) % videosPlaylist.length
}

const ultimoChamado = computed(() => chamadosStore.ultimoChamado)
const timerChamadoRef = ref<ReturnType<typeof setTimeout> | null>(null)
const chamadoAtualIdRef = ref<number | null>(null)

function limparTimerChamado() {
  if (timerChamadoRef.value) {
    clearTimeout(timerChamadoRef.value)
    timerChamadoRef.value = null
  }
  chamadoAtualIdRef.value = null
}

function agendarConclusaoAutomatica(chamadoId: number) {
  limparTimerChamado()
  chamadoAtualIdRef.value = chamadoId
  timerChamadoRef.value = setTimeout(async () => {
    if (chamadoAtualIdRef.value === chamadoId && clinicaId.value) {
      try {
        await chamadosStore.concluirChamadoPublico(chamadoId, clinicaId.value)
      } catch (error) {
        console.error('Erro ao concluir chamado automaticamente', error)
      }
    }
  }, 10000)
}

watch(ultimoChamado, (novoChamado) => {
  if (novoChamado && novoChamado.id !== chamadoAtualIdRef.value) {
    agendarConclusaoAutomatica(novoChamado.id)
  } else if (!novoChamado) {
    limparTimerChamado()
  }
})

const ultimasChamadas = computed(() => chamadosStore.historicoChamados.slice(0, 4))
const unidadeLabel = computed(() => unidade.value?.nome || (clinicaId.value ? `Unidade ${clinicaId.value}` : 'Unidade'))
const mostrarDesbloqueioAudio = computed(() => !audioAtivo.value && !painelError.value)
const mensagemAudio = computed(() => audioBloqueado.value
  ? 'Áudio bloqueado pelo navegador'
  : 'Tentando ativar áudio automaticamente')
</script>

<template>
  <div
    class="relative flex h-screen flex-col gap-4 overflow-hidden p-6"
    tabindex="0"
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
      <header class="flex shrink-0 items-center justify-between">
        <div class="flex items-center gap-3">
          <LogoMed :tipo="0" />
          <UBadge
            :label="unidadeLabel"
            color="primary"
            variant="soft"
            size="lg"
          />
          <UButton
            v-if="!audioAtivo"
            icon="i-lucide-volume-2"
            :label="audioBloqueado ? 'Ativar áudio' : 'Ativando áudio'"
            color="primary"
            variant="soft"
            :loading="audioAtivando"
            @click.stop="ativarAudioPorInteracao"
          />
          <div
            v-else-if="ttsLoading"
            class="flex items-center gap-1 text-sm text-muted"
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
        <div class="text-right">
          <p class="text-2xl font-light text-muted">
            {{ dataFormatada }}
          </p>
          <p class="text-5xl font-bold tracking-tight text-foreground tabular-nums">
            {{ horaFormatada }}
          </p>
        </div>
      </header>

      <div class="flex min-h-0 flex-1 gap-4">
        <div class="flex min-w-0 flex-2 flex-col gap-4">
          <template v-if="ultimoChamado">
            <UCard class="flex flex-1 flex-col items-center justify-center bg-primary-600 p-10 dark:bg-primary-700/80">
              <div class="w-full">
                <p class="mb-4 text-center text-xl font-medium uppercase tracking-widest text-white">
                  Chamando Agora
                </p>

                <p class="mb-6 text-center text-5xl font-bold leading-tight text-white md:text-7xl">
                  {{ ultimoChamado.pacienteNome }}
                </p>
              </div>

              <div class="mb-6 flex w-full flex-col items-center justify-center gap-4">
                <UPageCard
                  class="w-full flex-1 bg-white/20 p-2! text-center"
                  variant="subtle"
                  :ui="{ container: 'p-0 sm:p-0' }"
                >
                  <p class="text-lg uppercase tracking-wider text-white">
                    Local de Atendimento
                  </p>
                  <p class="text-4xl font-semibold text-white">
                    {{ ultimoChamado.localAtendimento }}
                  </p>
                </UPageCard>
                <UPageCard
                  class="w-full flex-1 bg-white/20 p-2! text-center"
                  variant="subtle"
                  :ui="{ container: 'p-0 sm:p-0' }"
                >
                  <p class="text-lg uppercase tracking-wider text-white">
                    Médico Responsável
                  </p>
                  <p class="text-4xl font-semibold text-white">
                    {{ ultimoChamado.medicoResponsavel || 'Atendimento' }}
                  </p>
                </UPageCard>
              </div>

              <div class="flex items-center justify-center gap-3">
                <UIcon
                  name="i-lucide-arrow-right"
                  class="animate-pulse text-white"
                />
                <p class="animate-pulse text-center text-3xl font-medium text-white">
                  Por favor, dirija-se à sala indicada.
                </p>
              </div>
            </UCard>
          </template>

          <template v-else>
            <UCard class="flex flex-1 flex-col items-center justify-center bg-primary-600 p-10 dark:bg-primary-700/80">
              <video
                ref="videoRef"
                :key="videoIndexAtual"
                class="rounded-xl"
                width="1100"
                height="619"
                autoplay
                muted
                playsinline
                @ended="avancarVideo"
              >
                <source
                  :src="videosPlaylist[videoIndexAtual]"
                  type="video/mp4"
                >
              </video>
            </UCard>
          </template>
        </div>

        <UCard
          class="flex flex-1 flex-col overflow-hidden"
          :ui="{ body: 'p-0 md:p-0 lg:p-0' }"
        >
          <template #title>
            <div class="flex items-start gap-3">
              <UIcon
                name="i-lucide-list-check"
                class="shrink-0 text-2xl text-primary"
              />
              <p class="text-lg font-bold uppercase tracking-widest text-primary">
                Últimas Chamadas
              </p>
            </div>
          </template>

          <div
            v-if="ultimasChamadas.length"
            class="flex flex-1 flex-col justify-center gap-2 overflow-hidden p-2"
          >
            <UCard
              v-for="chamado in ultimasChamadas"
              :key="chamado.id"
            >
              <p class="truncate text-2xl font-semibold text-foreground">
                {{ chamado.pacienteNome }}
              </p>
              <div class="mt-1 flex justify-between text-sm text-muted">
                <UBadge
                  :label="chamado.localAtendimento"
                  color="primary"
                  variant="soft"
                  size="lg"
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
      </div>

      <div
        v-if="mostrarDesbloqueioAudio"
        class="absolute inset-0 z-20 flex items-center justify-center bg-neutral-950/65 p-6 backdrop-blur-sm"
        @click.stop="ativarAudioPorInteracao"
      >
        <UCard
          class="max-w-xl text-center shadow-2xl"
          :ui="{ body: 'p-8 sm:p-10' }"
        >
          <div class="mx-auto mb-5 flex size-20 items-center justify-center rounded-full bg-primary/10">
            <UIcon
              name="i-lucide-volume-2"
              class="text-5xl text-primary"
            />
          </div>
          <p class="mb-2 text-3xl font-bold text-foreground">
            Iniciar painel com áudio
          </p>
          <p class="mb-6 text-lg text-muted">
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
