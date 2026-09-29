import type { AgendamentoComPaciente } from '~/features/atendimentos/types'

const SEGUNDOS_BLOQUEIO_CHAMADA = 5

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

/**
 * Chamada de paciente para o painel, compartilhada entre dashboard e tela de
 * atendimento. O estado (envio/contagem) é local a cada componente que usa.
 */
export function useChamarPaciente() {
  const auth = useAuthStore()
  const chamadosStore = useChamadosStore()
  const toast = useToast()
  const { sala } = useSalaAtendimento()

  const callingState = ref<{ pacienteId: number, secondsLeft: number } | null>(null)
  const chamadaEmEnvio = ref<number | null>(null)
  const salaModalAberto = ref(false)
  // Chamada que aguarda a escolha do consultório para ser enviada.
  let chamadaPendente: AgendamentoComPaciente | null = null
  let callingInterval: ReturnType<typeof setInterval> | null = null

  function limparIntervalo() {
    if (callingInterval) {
      clearInterval(callingInterval)
      callingInterval = null
    }
  }

  onUnmounted(limparIntervalo)

  function isChamadaBloqueada(pacienteId: number) {
    return chamadaEmEnvio.value === pacienteId || callingState.value?.pacienteId === pacienteId
  }

  function rotuloChamada(pacienteId: number) {
    if (chamadaEmEnvio.value === pacienteId) return 'Chamando'
    if (callingState.value?.pacienteId === pacienteId) return String(callingState.value.secondsLeft)
    return 'Chamar'
  }

  function iniciarContagem(pacienteId: number) {
    limparIntervalo()
    callingState.value = { pacienteId, secondsLeft: SEGUNDOS_BLOQUEIO_CHAMADA }
    callingInterval = setInterval(() => {
      if (callingState.value && callingState.value.secondsLeft > 1) {
        callingState.value = { ...callingState.value, secondsLeft: callingState.value.secondsLeft - 1 }
      } else {
        callingState.value = null
        limparIntervalo()
      }
    }, 1000)
  }

  async function chamar(ag: AgendamentoComPaciente) {
    if (isChamadaBloqueada(ag.paciente.id)) return

    if (!sala.value) {
      chamadaPendente = ag
      salaModalAberto.value = true
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
      await chamadosStore.chamarPaciente(
        ag.paciente.id,
        ag.paciente.nomeSocial || ag.paciente.nome,
        `Consultório ${sala.value}`,
        auth.user?.nome ?? 'Dr.',
        clinicaId
      )
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

    iniciarContagem(ag.paciente.id)
  }

  // Chamar após salvar o consultório no modal, se havia uma chamada pendente.
  function aoDefinirSala() {
    const pendente = chamadaPendente
    chamadaPendente = null
    if (pendente) void chamar(pendente)
  }

  // Fechar o modal sem salvar descarta a chamada pendente. (O evento "salva" é
  // emitido de forma síncrona, antes deste watcher rodar.)
  watch(salaModalAberto, (aberto) => {
    if (!aberto) chamadaPendente = null
  })

  return {
    chamar,
    isChamadaBloqueada,
    rotuloChamada,
    salaModalAberto,
    aoDefinirSala
  }
}
