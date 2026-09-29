import { defineStore } from 'pinia'
import type { Paciente } from '~/types'
import {
  atualizarStatusAgendamento,
  listarAgendamentos,
  type ConsultaStatusPayload,
  type AtualizarStatusAgendamentoResponse
} from '../services/agendaService'
import type { Agendamento, AgendamentoComPaciente, AgendamentoStatus } from '../types'
import { minutosDoHorario, normalizarHorario } from '~/utils/time'

type AgendaSnapshotEvent = {
  data?: string
  items: AgendamentoComPaciente[]
}

type AgendamentoStatusEvent = {
  id: number
  status: AgendamentoStatus
  pacienteId?: number
}

export const useAgendamentosStore = defineStore('agendamentos', () => {
  const agendamentos = ref<AgendamentoComPaciente[]>([])
  const loading = ref(true)
  // Data (YYYY-MM-DD) cuja agenda está efetivamente carregada no store.
  const dataCarregada = ref<string | null>(null)
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
      return minutosDoHorario(a.horario) - minutosDoHorario(b.horario)
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
      if (isAgendamentoComPaciente(evento)) {
        agendamentos.value.push({ ...evento, horario: normalizarHorario(evento.horario) })
      }
      return
    }

    if (isAgendamentoComPaciente(evento)) {
      agendamentos.value[index] = { ...evento, horario: normalizarHorario(evento.horario) }
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

      agendamentos.value = payload.items.map(item => ({ ...item, horario: normalizarHorario(item.horario) }))
      dataCarregada.value = payload.data ?? filtrosAtuais.data ?? null
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
      const raw = await listarAgendamentos({ clinicaId, data, medicoId })
      // Os filtros mudaram durante a requisição (ex.: retomada de um atendimento
      // pendente de outro dia); descarta a resposta para não sobrescrever o store.
      if (filtrosAtuais.data !== data) return

      if (raw.every(a => 'paciente' in a)) {
        agendamentos.value = (raw as AgendamentoComPaciente[]).map(item => ({ ...item, horario: normalizarHorario(item.horario) }))
        dataCarregada.value = data ?? null
        return
      }

      const allPacientes = await $fetch<Paciente[]>('/api/pacientes')
      const pacienteMap = new Map(allPacientes.map(p => [p.id, p]))

      agendamentos.value = (raw as Agendamento[])
        .filter(a => pacienteMap.has(a.pacienteId))
        .map(a => ({
          ...a,
          horario: normalizarHorario(a.horario),
          paciente: pacienteMap.get(a.pacienteId)!
        }))
      dataCarregada.value = data ?? null
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

  // Coloca no store apenas um atendimento pendente (possivelmente de outro dia) para
  // retomá-lo na tela de atendimento. Ajusta os filtros para a data dele, assim os
  // snapshots do SSE da agenda de hoje não o removem enquanto o médico o conclui.
  function focarAtendimento(ag: AgendamentoComPaciente) {
    const data = ag.data?.slice(0, 10)
    filtrosAtuais = { ...filtrosAtuais, clinicaId: ag.clinicaId ?? filtrosAtuais.clinicaId, data }
    agendamentos.value = [{ ...ag, horario: normalizarHorario(ag.horario) }]
    dataCarregada.value = data ?? null
    loading.value = false
  }

  async function atualizarStatus(id: number, status: AgendamentoStatus, consulta?: ConsultaStatusPayload, clinicaId?: number) {
    try {
      const clinicaIdEfetiva = clinicaId
        ?? agendamentos.value.find(a => a.id === id)?.clinicaId
        ?? filtrosAtuais.clinicaId

      const atualizado = await atualizarStatusAgendamento(id, status, consulta, clinicaIdEfetiva)
      const completo = atualizado as AtualizarStatusAgendamentoResponse
      aplicarStatusAgendamento(isAgendamentoComPaciente(completo) ? completo : { id, status })
      return atualizado
    } catch (error) {
      console.error('Erro ao atualizar status do agendamento')
      throw error
    }
  }

  return {
    agendamentos,
    loading,
    dataCarregada,
    emAtendimento,
    fila,
    ordenados,
    totalAgendamentos,
    totalAtendidos,
    totalFaltas,
    init,
    fetchAgendamentos,
    focarAtendimento,
    atualizarStatus
  }
})
