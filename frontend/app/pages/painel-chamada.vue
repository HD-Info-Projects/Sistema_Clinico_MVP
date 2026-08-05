<script setup lang="ts">
import { useSse } from '~/composables/useSse'

const chamadosStore = useChamadosStore()

const audioRef = ref<HTMLAudioElement | null>(null)
const audioUrl = ref<string | null>(null)
const audioAtivo = ref(false)
const ttsLoading = ref(false)
const ttsError = ref(false)
const ttsRequestId = ref(0)
const ttsAbortController = ref<AbortController | null>(null)

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
    URL.revokeObjectURL(url)
  }
}

function limparAudioAtual() {
  audioRef.value?.pause()
  audioRef.value = null

  if (audioUrl.value) {
    URL.revokeObjectURL(audioUrl.value)
    audioUrl.value = null
  }
}

async function ativarAudio() {
  ttsError.value = false
  audioAtivo.value = await testarAudioPermitido()
}

async function falarChamado(pacienteNome: string, localAtendimento: string) {
  if (!audioAtivo.value) return

  const requestId = ttsRequestId.value + 1
  ttsRequestId.value = requestId
  ttsAbortController.value?.abort()

  const abortController = new AbortController()
  ttsAbortController.value = abortController
  const texto = `${pacienteNome}, por favor dirija-se à ${localAtendimento}`

  limparAudioAtual()
  ttsLoading.value = true
  ttsError.value = false

  try {
    const res = await fetch('/api/tts/speak', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text: texto }),
      signal: abortController.signal
    })

    if (!res.ok) throw new Error('Erro ao gerar áudio')
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
      ttsLoading.value = false
      ttsError.value = false
      limparAudioAtual()
      return
    }

    ttsLoading.value = false
    ttsError.value = true
    limparAudioAtual()
  }
}

onMounted(async () => {
  audioAtivo.value = await testarAudioPermitido()

  chamadosStore.init({ public: true })

  const sse = useSse()
  sse.on('chamado:novo', (data: unknown) => {
    const chamado = data as { pacienteNome?: string, localAtendimento?: string }
    if (chamado?.pacienteNome) {
      void falarChamado(chamado.pacienteNome, chamado.localAtendimento ?? 'sala de atendimento')
    }
  })
  sse.connect({ public: true })
})

onBeforeUnmount(() => {
  ttsRequestId.value += 1
  ttsAbortController.value?.abort()
  limparAudioAtual()
})

const { horaFormatada, dataFormatada } = useRelogio()

const ultimoChamado = computed(() => chamadosStore.ultimoChamado)
const ultimasChamadas = computed(() => chamadosStore.historicoChamados.slice(0, 4))
</script>

<template>
  <div class="flex flex-col h-screen p-6 gap-4 overflow-hidden">
    <header class="flex items-center justify-between shrink-0">
      <div class="flex items-center gap-3">
        <LogoMed :tipo="0" />
        <UButton
          v-if="!audioAtivo"
          icon="i-lucide-volume-2"
          label="Ativar áudio"
          color="primary"
          variant="soft"
          @click="ativarAudio"
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
          Erro no áudio
        </div>
        <UBadge
          v-else
          icon="i-lucide-volume-2"
          label="Áudio ativo"
          color="success"
          variant="soft"
        />
      </div>
      <div class="text-right">
        <p class="text-2xl font-light text-muted">
          {{ dataFormatada }}
        </p>
        <p class="text-5xl font-bold tabular-nums tracking-tight text-foreground">
          {{ horaFormatada }}
        </p>
      </div>
    </header>

    <div class="flex-1 flex gap-4 min-h-0">
      <div class="flex-2 flex flex-col gap-4 min-w-0">
        <template v-if="ultimoChamado">
          <UCard
            class="flex-1 flex flex-col items-center justify-center p-10 bg-primary-600 dark:bg-primary-700/80"
          >
            <div class="w-full">
              <p class="text-xl font-medium text-white text-center tracking-widest uppercase mb-4">
                Chamando Agora
              </p>

              <p class="text-5xl md:text-7xl font-bold text-center text-white leading-tight mb-6">
                {{ ultimoChamado.pacienteNome }}
              </p>
            </div>

            <div class="flex flex-col gap-4 w-full mb-6 justify-center items-center">
              <UPageCard
                class="flex-1 bg-white/20 text-center p-2! w-full"
                variant="subtle"
                :ui="{ container: 'p-0 sm:p-0' }"
              >
                <p class="text-lg text-white uppercase tracking-wider">
                  Local de Atendimento
                </p>
                <p class="text-4xl font-semibold text-foreground text-white">
                  {{ ultimoChamado.localAtendimento }}
                </p>
              </UPageCard>
              <UPageCard
                class="flex-1 bg-white/20 text-center p-2! w-full"
                variant="subtle"
                :ui="{ container: 'p-0 sm:p-0' }"
              >
                <p class="text-lg text-white uppercase tracking-wider">
                  Médico Responsável
                </p>
                <p class="text-4xl font-semibold text-foreground text-white">
                  {{ ultimoChamado.medicoResponsavel }}
                </p>
              </UPageCard>
            </div>

            <div class="flex items-center gap-3 justify-center">
              <UIcon
                name="i-lucide-arrow-right"
                class="text-white animate-pulse"
              />
              <p class="text-3xl text-center text-white font-medium animate-pulse">
                Por favor, dirija-se à sala indicada.
              </p>
            </div>
          </UCard>
        </template>

        <template v-else>
          <UCard class="flex-1 flex flex-col items-center justify-center p-10 bg-primary-600 dark:bg-primary-700/80">
            <UIcon
              name="i-lucide-stethoscope"
              class="text-7xl text-white"
            />
            <p class="text-2xl font-medium text-white mt-4">
              Nenhuma chamada no momento
            </p>
            <p class="text-base text-white mt-1">
              A lista de chamadas aparecerá aqui automaticamente.
            </p>
          </UCard>
        </template>
      </div>

      <UCard
        class="flex-1 flex flex-col overflow-hidden"
        :ui="{ body: 'p-0 md:p-0 lg:p-0' }"
      >
        <template #title>
          <div class="flex items-start gap-3">
            <UIcon
              name="i-lucide-list-check"
              class="text-2xl text-primary shrink-0"
            />
            <p class="text-lg font-bold text-primary tracking-widest uppercase">
              Últimas Chamadas
            </p>
          </div>
        </template>

        <div
          v-if="ultimasChamadas.length"
          class="flex-1 flex flex-col justify-center gap-2 p-2 overflow-hidden"
        >
          <UCard
            v-for="chamado in ultimasChamadas"
            :key="chamado.id"
          >
            <p class="text-2xl font-semibold text-foreground truncate">
              {{ chamado.pacienteNome }}
            </p>
            <div class="flex justify-between text-sm text-muted mt-1">
              <UBadge
                :label="chamado.localAtendimento"
                color="primary"
                variant="soft"
                size="lg"
              />
              <span>
                {{ chamado.dataChamada }}</span>
            </div>
          </UCard>
        </div>

        <div
          v-else
          class="flex-1 flex items-center justify-center"
        >
          <p class="text-base text-muted">
            Nenhuma chamada realizada
          </p>
        </div>
      </UCard>
    </div>
  </div>
</template>
