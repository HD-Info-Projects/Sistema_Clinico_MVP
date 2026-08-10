import { defineStore } from 'pinia'
import type { Agendamento, AgendamentoComPaciente, AgendamentoStatus, ExameConsultaPayload, Paciente } from '~/types'

type AgendaSnapshotEvent = {
  data?: string
  items: AgendamentoComPaciente[]
}

type AgendamentoStatusEvent = {
  id: number
  status: AgendamentoStatus
  pacienteId?: number
}

type ConsultaStatusPayload = {
  anamnese?: string
  diagnosticos?: { cid: string, descricao?: string, principal: boolean }[]
  medicamentos?: string
  exames?: ExameConsultaPayload[]
  duracao?: number
}

export const useAgendamentosStore = defineStore('agendamentos', () => {
  const agendamentos = ref<AgendamentoComPaciente[]>([])
  const loading = ref(true)
  let sse: ReturnType<typeof useSse> | null = null
  let sseHandlersRegistrados = false
  let filtrosAtuais: {
    clinicaId?: number
    data?: string
    medicoId?: number
  } = {}

  const emAtendimento = computed(() =>
    agendamentos.value.find(a => a.status === 'em-atendimento') ?? null
  )

  const fila = computed(() =>
    agendamentos.value.filter(a => a.status === 'em-espera')
  )

  const totalAgendamentos = computed(() => agendamentos.value.length)
  const totalAtendidos = computed(() => agendamentos.value.filter(a => a.status === 'atendido').length)
  const totalFaltas = computed(() => agendamentos.value.filter(a => a.status === 'faltou').length)

  const ordemStatus: Record<string, number> = {
    'agendado': 0,
    'em-espera': 1,
    'em-atendimento': 2,
    'atendido': 3,
    'faltou': 4
  }

  const ordenados = computed(() =>
    [...agendamentos.value].sort((a, b) => {
      const statusDiff = (ordemStatus[a.status] ?? 99) - (ordemStatus[b.status] ?? 99)
      if (statusDiff !== 0) return statusDiff
      return a.horario.localeCompare(b.horario)
    })
  )

  function isAgendamentoComPaciente(value: unknown): value is AgendamentoComPaciente {
    return Boolean(value && typeof value === 'object' && 'paciente' in value)
  }

  function atualizarFiltros(clinicaId?: number, data?: string, medicoId?: number) {
    filtrosAtuais = { clinicaId, data, medicoId }
  }

  function aplicarStatusAgendamento(evento: AgendamentoStatusEvent | AgendamentoComPaciente) {
    const index = agendamentos.value.findIndex(ag => ag.id === evento.id)

    if (index === -1) {
      if (isAgendamentoComPaciente(evento)) agendamentos.value.push(evento)
      return
    }

    if (isAgendamentoComPaciente(evento)) {
      agendamentos.value[index] = evento
      return
    }

    agendamentos.value[index] = {
      ...agendamentos.value[index]!,
      status: evento.status
    }
  }

  function registrarSseHandlers() {
    if (sseHandlersRegistrados) return

    sse = useSse()

    sse.on('agenda:snapshot', (data: unknown) => {
      const payload = data as AgendaSnapshotEvent

      if (payload.data && filtrosAtuais.data && payload.data !== filtrosAtuais.data) return
      if (!Array.isArray(payload.items)) return

      agendamentos.value = payload.items
      loading.value = false
    })

    sse.on('agendamento:status', (data: unknown) => {
      const evento = data as AgendamentoStatusEvent | AgendamentoComPaciente
      if (!evento?.id || !evento.status) return

      aplicarStatusAgendamento(evento)
    })

    sseHandlersRegistrados = true
  }

  async function fetchAgendamentos(clinicaId?: number, data?: string, medicoId?: number) {
    atualizarFiltros(clinicaId, data, medicoId)
    loading.value = true

    try {
      const params = new URLSearchParams()
      if (clinicaId) params.set('clinicaId', String(clinicaId))
      if (data) params.set('data', data)
      if (medicoId) params.set('medicoId', String(medicoId))
      const qs = params.toString()

      const raw = await $fetch<(Agendamento | AgendamentoComPaciente)[]>(`/api/agendamentos${qs ? `?${qs}` : ''}`)

      if (raw.every(a => 'paciente' in a)) {
        agendamentos.value = raw as AgendamentoComPaciente[]
        return
      }

      const allPacientes = await $fetch<Paciente[]>('/api/pacientes')
      const pacienteMap = new Map(allPacientes.map(p => [p.id, p]))

      agendamentos.value = (raw as Agendamento[])
        .filter(a => pacienteMap.has(a.pacienteId))
        .map(a => ({
          ...a,
          paciente: pacienteMap.get(a.pacienteId)!
        }))
    } catch {
      console.error('Erro ao carregar agendamentos')
    } finally {
      loading.value = false
    }
  }

  async function init(clinicaId?: number, data?: string, medicoId?: number) {
    atualizarFiltros(clinicaId, data, medicoId)
    registrarSseHandlers()
    sse?.connect({ data, clinicaId })
    await fetchAgendamentos(clinicaId, data, medicoId)
  }

  async function atualizarStatus(id: number, status: AgendamentoStatus, consulta?: ConsultaStatusPayload, clinicaId?: number) {
    try {
      const clinicaIdEfetiva = clinicaId
        ?? agendamentos.value.find(a => a.id === id)?.clinicaId
        ?? filtrosAtuais.clinicaId
      const params = new URLSearchParams()
      if (clinicaIdEfetiva) params.set('clinicaId', String(clinicaIdEfetiva))
      const qs = params.toString()

      const atualizado = await $fetch<AgendamentoComPaciente>(`/api/agendamentos/${id}${qs ? `?${qs}` : ''}`, {
        method: 'PATCH',
        body: { status, consulta }
      })
      aplicarStatusAgendamento(isAgendamentoComPaciente(atualizado) ? atualizado : { id, status })
      return atualizado
    } catch (error) {
      console.error('Erro ao atualizar status do agendamento')
      throw error
    }
  }

  return {
    agendamentos,
    loading,
    emAtendimento,
    fila,
    ordenados,
    totalAgendamentos,
    totalAtendidos,
    totalFaltas,
    init,
    fetchAgendamentos,
    atualizarStatus
  }
})
