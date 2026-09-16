import { defineStore } from 'pinia'
import type { Chamado } from '../types'
import {
  buscarChamadoAtivo,
  concluirChamado as concluirChamadoApi,
  concluirChamadoPublico as concluirChamadoPublicoApi,
  criarChamado,
  listarHistoricoChamadas
} from '../services/chamadasService'

export const useChamadosStore = defineStore('chamados', () => {
  const chamados = ref<Chamado[]>([])
  const loading = ref(true)
  let sse: ReturnType<typeof useSse> | null = null
  let sseHandlersRegistrados = false
  let clinicaIdAtual: number | null | undefined = null

  const ultimoChamado = computed(() =>
    chamados.value.find(c => c.status === 'chamando') ?? null
  )

  const historicoChamados = computed(() => {
    const historico = chamados.value.filter(c => c.status !== 'chamando')
    return historico.filter((c, i) => {
      if (i === 0) return true
      const anterior = historico[i - 1]
      return anterior ? c.pacienteNome !== anterior.pacienteNome : true
    })
  })

  async function fetchChamados(clinicaId?: number | null) {
    try {
      const [ativa, historico] = await Promise.all([
        buscarChamadoAtivo(clinicaId),
        listarHistoricoChamadas(clinicaId)
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

  async function init(options?: { public?: boolean, clinicaId?: number | null, data?: string }) {
    sse = useSse()
    clinicaIdAtual = options?.clinicaId
    await fetchChamados(clinicaIdAtual)

    if (sseHandlersRegistrados) {
      sse.connect({ public: options?.public, clinicaId: options?.clinicaId, data: options?.data })
      return
    }

    sse.on('connected', () => {
      void fetchChamados(clinicaIdAtual)
    })
    sse.on('chamado:novo', (data: unknown) => {
      const chamado = data as Chamado
      const existingActive = chamados.value.findIndex(c => c.status === 'chamando')
      if (existingActive >= 0) {
        const active = chamados.value[existingActive]!
        const mesmoPaciente = Boolean(active.pacienteNome && chamado.pacienteNome && active.pacienteNome === chamado.pacienteNome)
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
    sse.connect({ public: options?.public, clinicaId: options?.clinicaId, data: options?.data })
  }

  async function chamarPaciente(pacienteId: number, pacienteNome: string, localAtendimento: string, medicoResponsavel: string, clinicaId?: number | null) {
    try {
      return await criarChamado({ pacienteId, pacienteNome, localAtendimento, medicoResponsavel }, clinicaId)
    } catch (error) {
      console.error('Erro ao chamar paciente')
      throw error
    }
  }

  async function concluirChamado(chamadoId: number, clinicaId?: number | null) {
    try {
      return await concluirChamadoApi(chamadoId, clinicaId)
    } catch (error) {
      console.error('Erro ao concluir chamado')
      throw error
    }
  }

  async function concluirChamadoPublico(chamadoId: number, clinicaId: number) {
    try {
      return await concluirChamadoPublicoApi(chamadoId, clinicaId)
    } catch (error) {
      console.error('Erro ao concluir chamado publicamente')
      throw error
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
    concluirChamado,
    concluirChamadoPublico
  }
})
