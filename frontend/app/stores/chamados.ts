import { defineStore } from 'pinia'
import type { Chamado } from '~/types'

export const useChamadosStore = defineStore('chamados', () => {
  const chamados = ref<Chamado[]>([])
  const loading = ref(true)
  let sse: ReturnType<typeof useSse> | null = null
  let sseHandlersRegistrados = false

  const ultimoChamado = computed(() =>
    chamados.value.find(c => c.status === 'chamando') ?? null
  )

  const historicoChamados = computed(() =>
    chamados.value.filter(c => c.status !== 'chamando')
  )

  async function fetchChamados() {
    try {
      const [ativa, historico] = await Promise.all([
        $fetch<Chamado | null>('/api/chamadas/ativa'),
        $fetch<Chamado[]>('/api/chamadas/historico')
      ])
      chamados.value = []
      if (ativa) chamados.value.push(ativa)
      chamados.value.push(...historico)
    } catch {
      console.error('Erro ao carregar chamados')
    } finally {
      loading.value = false
    }
  }

  async function init(options?: { public?: boolean }) {
    sse = useSse()
    await fetchChamados()

    if (sseHandlersRegistrados) {
      sse.connect({ public: options?.public })
      return
    }

    sse.on('chamado:novo', (data: unknown) => {
      const chamado = data as Chamado
      const existingActive = chamados.value.findIndex(c => c.status === 'chamando')
      if (existingActive >= 0) {
        const active = chamados.value[existingActive]!
        const mesmoPaciente = Boolean(active.pacienteId && chamado.pacienteId && active.pacienteId === chamado.pacienteId)
        if (active.id === chamado.id || mesmoPaciente) {
          chamados.value[existingActive] = chamado
          return
        }

        active.status = 'concluido'
      }
      chamados.value.unshift(chamado)
    })
    sse.on('chamado:concluido', (data: unknown) => {
      const chamado = data as Chamado
      const idx = chamados.value.findIndex(c => c.id === chamado.id)
      if (idx >= 0) chamados.value[idx] = chamado
    })
    sseHandlersRegistrados = true
    sse.connect({ public: options?.public })
  }

  async function chamarPaciente(pacienteId: number, pacienteNome: string, localAtendimento: string, medicoResponsavel: string) {
    try {
      await $fetch('/api/chamadas', {
        method: 'POST',
        body: { pacienteId, pacienteNome, localAtendimento, medicoResponsavel }
      })
    } catch {
      console.error('Erro ao chamar paciente')
    }
  }

  async function concluirChamado(chamadoId: number) {
    try {
      await $fetch(`/api/chamadas/${chamadoId}`, {
        method: 'PATCH',
        body: { status: 'concluido' }
      })
    } catch {
      console.error('Erro ao concluir chamado')
    }
  }

  return {
    chamados,
    loading,
    ultimoChamado,
    historicoChamados,
    init,
    fetchChamados,
    chamarPaciente,
    concluirChamado
  }
})
