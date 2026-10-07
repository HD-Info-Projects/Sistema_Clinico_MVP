import { defineStore } from 'pinia'
import type { Paciente } from '~/types'
import {
  atualizarStatusExameAgendamento,
  atualizarStatusAgendamento,
  listarAgendamentosExames,
  listarAgendamentos,
  verificarAtendimentoEmAndamento,
  type AtendimentoEmAndamentoResponse,
  type ConsultaStatusPayload,
  type AtualizarStatusAgendamentoResponse
} from '../services/agendaService'
import type { Agendamento, AgendamentoComPaciente, AgendamentoStatus } from '../types'
import { minutosDoHorario, normalizarHorario } from '~/utils/time'

type AgendaSnapshotEvent = {
  data?: string
  contexto?: AgendaContexto
  items: AgendamentoComPaciente[]
}

type AgendamentoStatusEvent = {
  id: number
  status: AgendamentoStatus
  emEdicao?: boolean
  pacienteId?: number
}

type AtendimentoPrioridadeEvent = {
  prioridadeOrigem: Agendamento['prioridadeOrigem']
  prioridadeSpdataId: number
  prioridade: boolean
}

type AgendaContexto = 'dashboard'
type AtendimentoAtualStatus = 'unknown' | 'loading' | 'present' | 'absent' | 'error'
type AtendimentoAtualResultado = (
  | { status: 'present', resumo: AtendimentoEmAndamentoResponse }
  | { status: 'absent' }
  | { status: 'error' }
  | { status: 'cancelled' }
)

export const useAgendamentosStore = defineStore('agendamentos', () => {
  const agendamentos = ref<AgendamentoComPaciente[]>([])
  const loading = ref(true)
  // Data (YYYY-MM-DD) cuja agenda está efetivamente carregada no store.
  const dataCarregada = ref<string | null>(null)
  const clinicaCarregada = ref<number | null>(null)
  const medicoCarregado = ref<number | null>(null)
  const contextoCarregado = ref<AgendaContexto | null>(null)
  const atendimentoAtualStatus = ref<AtendimentoAtualStatus>('unknown')
  const atendimentoAtualResumo = ref<AtendimentoEmAndamentoResponse | null>(null)
  let sse: ReturnType<typeof useSse> | null = null
  let sseHandlersRegistrados = false
  let fetchRequestId = 0
  let mutacoesStatusPendentes = 0
  let atendimentoAtualRequestId = 0
  let atendimentoAtualChave: string | null = null
  let atendimentoAtualVerificadoEm = 0
  let verificacaoAtendimentoAtual: Promise<AtendimentoAtualResultado> | null = null
  let filtrosAtuais: {
    clinicaId?: number
    data?: string
    medicoId?: number
    contexto?: AgendaContexto
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

  function atualizarFiltros(clinicaId?: number, data?: string, medicoId?: number, contexto?: AgendaContexto) {
    filtrosAtuais = { clinicaId, data, medicoId, contexto }
  }

  function marcarContextoCarregado(clinicaId?: number, data?: string, medicoId?: number, contexto?: AgendaContexto) {
    dataCarregada.value = data ?? null
    clinicaCarregada.value = clinicaId ?? null
    medicoCarregado.value = medicoId ?? null
    contextoCarregado.value = contexto ?? null
  }

  function limparContextoCarregado() {
    dataCarregada.value = null
    clinicaCarregada.value = null
    medicoCarregado.value = null
    contextoCarregado.value = null
  }

  function contextoAtualEh(clinicaId?: number, data?: string, medicoId?: number, contexto?: AgendaContexto) {
    return dataCarregada.value === (data ?? null)
      && clinicaCarregada.value === (clinicaId ?? null)
      && medicoCarregado.value === (medicoId ?? null)
      && contextoCarregado.value === (contexto ?? null)
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
      status: evento.status,
      emEdicao: evento.emEdicao ?? agendamentos.value[index]!.emEdicao
    }
  }

  function resumoAtendimento(item: AgendamentoComPaciente): AtendimentoEmAndamentoResponse {
    return {
      emAtendimento: true,
      emEdicao: item.emEdicao,
      data: item.data,
      unidadeId: item.clinicaId,
      id: item.id,
      medsystemAtendimentoId: item.medsystemAtendimentoId ?? undefined,
      paciente: {
        id: item.paciente.id,
        nome: item.paciente.nome,
        nomeSocial: item.paciente.nomeSocial
      }
    }
  }

  function marcarAtendimentoAtual(
    item: AgendamentoComPaciente | null,
    chaveEsperada = atendimentoAtualChave
  ) {
    if (chaveEsperada !== atendimentoAtualChave) return false
    if (
      item
      && atendimentoAtualChave
      && !atendimentoAtualChave.endsWith(`:${item.clinicaId}`)
    ) return false

    atendimentoAtualRequestId++
    verificacaoAtendimentoAtual = null
    atendimentoAtualResumo.value = item ? resumoAtendimento(item) : null
    atendimentoAtualStatus.value = item ? 'present' : 'absent'
    atendimentoAtualVerificadoEm = Date.now()
    return true
  }

  function invalidarAtendimentoAtual() {
    fetchRequestId++
    atendimentoAtualRequestId++
    atendimentoAtualChave = null
    verificacaoAtendimentoAtual = null
    atendimentoAtualResumo.value = null
    atendimentoAtualStatus.value = 'unknown'
    atendimentoAtualVerificadoEm = 0
  }

  async function verificarAtendimentoAtual(chave: string, force = false) {
    if (mutacoesStatusPendentes) return { status: 'cancelled' as const }
    if (atendimentoAtualChave === chave && verificacaoAtendimentoAtual) {
      return verificacaoAtendimentoAtual
    }

    if (!force && atendimentoAtualChave === chave) {
      if (
        Date.now() - atendimentoAtualVerificadoEm < 5_000
        && (atendimentoAtualStatus.value === 'present' || atendimentoAtualStatus.value === 'absent')
      ) {
        return atendimentoAtualResumo.value
          ? { status: 'present' as const, resumo: atendimentoAtualResumo.value }
          : { status: 'absent' as const }
      }
    }

    const requestId = ++atendimentoAtualRequestId
    atendimentoAtualChave = chave
    atendimentoAtualStatus.value = 'loading'

    const verificacao = verificarAtendimentoEmAndamento()
      .then((resultado) => {
        if (requestId !== atendimentoAtualRequestId || atendimentoAtualChave !== chave) {
          return { status: 'cancelled' as const }
        }

        atendimentoAtualResumo.value = resultado.emAtendimento ? resultado : null
        atendimentoAtualStatus.value = resultado.emAtendimento ? 'present' : 'absent'
        atendimentoAtualVerificadoEm = Date.now()
        const local = emAtendimento.value
        if (local && resultado.emAtendimento && resultado.id === local.id && resultado.emEdicao !== undefined) {
          aplicarStatusAgendamento({ id: local.id, status: local.status, emEdicao: resultado.emEdicao })
        }
        if (local && (!resultado.emAtendimento || (resultado.id && resultado.id !== local.id))) {
          agendamentos.value = agendamentos.value.filter(item => item.id !== local.id)
        }
        return resultado.emAtendimento
          ? { status: 'present' as const, resumo: resultado }
          : { status: 'absent' as const }
      })
      .catch(() => {
        if (requestId !== atendimentoAtualRequestId || atendimentoAtualChave !== chave) {
          return { status: 'cancelled' as const }
        }
        atendimentoAtualStatus.value = 'error'
        return { status: 'error' as const }
      })
      .finally(() => {
        if (requestId === atendimentoAtualRequestId) verificacaoAtendimentoAtual = null
      })

    verificacaoAtendimentoAtual = verificacao
    return verificacao
  }

  async function garantirAtendimentoAtual(params: {
    chave: string
    clinicaId?: number
    medicoId?: number
    force?: boolean
  }) {
    const chaveEsperada = params.chave
    let resumo = atendimentoAtualResumo.value
    const local = emAtendimento.value
    const verificacaoRecente = Date.now() - atendimentoAtualVerificadoEm < 5_000

    if (
      atendimentoAtualChave === params.chave
      && atendimentoAtualStatus.value === 'present'
      && verificacaoRecente
      && !params.force
      && local
      && (!resumo?.id || resumo.id === local.id)
    ) {
      return { status: 'present' as const, resumo: resumo ?? resumoAtendimento(local) }
    }

    if (
      params.force
      || atendimentoAtualChave !== params.chave
      || atendimentoAtualStatus.value !== 'present'
      || !verificacaoRecente
    ) {
      const resultado = await verificarAtendimentoAtual(params.chave, params.force)
      if (resultado.status === 'cancelled') {
        const atendimentoAtual = emAtendimento.value
        const resumoAtual = atendimentoAtualResumo.value
        if (
          atendimentoAtualChave === params.chave
          && atendimentoAtualStatus.value === 'present'
          && atendimentoAtual
          && (!resumoAtual?.id || resumoAtual.id === atendimentoAtual.id)
        ) {
          return {
            status: 'present' as const,
            resumo: resumoAtual ?? resumoAtendimento(atendimentoAtual)
          }
        }
      }
      if (resultado.status !== 'present') return resultado
      resumo = resultado.resumo
    }

    if (atendimentoAtualChave !== chaveEsperada) return { status: 'cancelled' as const }
    if (!resumo?.emAtendimento) return { status: 'absent' as const }
    if (!resumo.data) return { status: 'error' as const }
    if (resumo.unidadeId && params.clinicaId && resumo.unidadeId !== params.clinicaId) {
      atendimentoAtualStatus.value = 'error'
      return { status: 'error' as const }
    }

    const confirmadoLocal = emAtendimento.value
    if (confirmadoLocal && resumo.id === confirmadoLocal.id && confirmadoLocal.clinicaId === params.clinicaId) {
      return { status: 'present' as const, resumo }
    }

    const carregamento = await fetchAgendamentos(
      resumo.unidadeId ?? params.clinicaId,
      resumo.data,
      params.medicoId,
      'dashboard'
    )

    if (atendimentoAtualChave !== chaveEsperada) return { status: 'cancelled' as const }
    if (carregamento === 'cancelled') {
      const atendimentoAtual = emAtendimento.value
      if (
        atendimentoAtualStatus.value === 'present'
        && atendimentoAtualResumo.value?.id === resumo.id
        && atendimentoAtual
        && (!resumo.id || resumo.id === atendimentoAtual.id)
      ) {
        return { status: 'present' as const, resumo: resumoAtendimento(atendimentoAtual) }
      }
      return { status: 'cancelled' as const }
    }
    if (carregamento === 'error') {
      atendimentoAtualStatus.value = 'error'
      return { status: 'error' as const }
    }

    const atendimento = emAtendimento.value
    if (!atendimento || (resumo.id && atendimento.id !== resumo.id)) {
      atendimentoAtualStatus.value = 'error'
      return { status: 'error' as const }
    }

    if (!marcarAtendimentoAtual(atendimento, chaveEsperada)) {
      return { status: 'cancelled' as const }
    }
    return { status: 'present' as const, resumo: resumoAtendimento(atendimento) }
  }

  function registrarSseHandlers() {
    if (sseHandlersRegistrados) return

    sse = useSse()

    sse.on('connected', (data: unknown) => {
      if (!(data as { reconnected?: boolean })?.reconnected) return
      const chave = atendimentoAtualChave
      void fetchAgendamentos(
        filtrosAtuais.clinicaId,
        filtrosAtuais.data,
        filtrosAtuais.medicoId,
        filtrosAtuais.contexto
      ).then(() => {
        if (chave && chave === atendimentoAtualChave) {
          void verificarAtendimentoAtual(chave, true)
        }
      })
    })

    sse.on('agenda:snapshot', (data: unknown) => {
      if (mutacoesStatusPendentes) return
      const payload = data as AgendaSnapshotEvent

      if (payload.data && filtrosAtuais.data && payload.data !== filtrosAtuais.data) return
      if (payload.contexto !== filtrosAtuais.contexto) return
      if (!Array.isArray(payload.items)) return

      // A snapshot may have been prepared before the successful PATCH. Keep
      // the active record until the dedicated endpoint confirms its state.
      const ativo = emAtendimento.value
      const items = payload.items.map(item => ({ ...item, horario: normalizarHorario(item.horario) }))
      if (ativo && atendimentoAtualResumo.value?.id === ativo.id) {
        const index = items.findIndex(item => item.id === ativo.id)
        if (index === -1) items.push(ativo)
        else items[index] = ativo
      }
      agendamentos.value = items
      marcarContextoCarregado(filtrosAtuais.clinicaId, payload.data ?? filtrosAtuais.data, filtrosAtuais.medicoId, filtrosAtuais.contexto)
      loading.value = false
      if (atendimentoAtualChave) {
        void verificarAtendimentoAtual(atendimentoAtualChave, true)
      }
    })

    sse.on('agendamento:status', (data: unknown) => {
      const evento = data as AgendamentoStatusEvent | AgendamentoComPaciente
      if (!evento?.id || !evento.status) return

      const eraAtendimentoAtual = emAtendimento.value?.id === evento.id
      aplicarStatusAgendamento(evento)
      if (evento.status === 'em-atendimento') {
        const atendimento = isAgendamentoComPaciente(evento)
          ? evento
          : agendamentos.value.find(item => item.id === evento.id) ?? null
        if (atendimento) {
          marcarAtendimentoAtual(atendimento)
        } else if (atendimentoAtualChave) {
          void verificarAtendimentoAtual(atendimentoAtualChave, true)
        } else {
          invalidarAtendimentoAtual()
        }
      } else if (eraAtendimentoAtual) {
        marcarAtendimentoAtual(null)
      }
    })

    sse.on('atendimento:prioridade', (data: unknown) => {
      const evento = data as AtendimentoPrioridadeEvent
      if ((evento?.prioridadeOrigem !== 'agenda' && evento?.prioridadeOrigem !== 'atendimento')
        || !Number.isInteger(evento.prioridadeSpdataId)
        || typeof evento.prioridade !== 'boolean') return

      agendamentos.value = agendamentos.value.map(agendamento => (
        agendamento.prioridadeOrigem === evento.prioridadeOrigem
        && agendamento.prioridadeSpdataId === evento.prioridadeSpdataId
          ? { ...agendamento, prioridade: evento.prioridade ? 'prioridade' : 'normal' }
          : agendamento
      ))
    })

    sseHandlersRegistrados = true
  }

  async function fetchAgendamentos(clinicaId?: number, data?: string, medicoId?: number, contexto?: AgendaContexto) {
    if (mutacoesStatusPendentes) return 'cancelled'
    const requestId = ++fetchRequestId
    if (!contextoAtualEh(clinicaId, data, medicoId, contexto)) {
      agendamentos.value = []
      limparContextoCarregado()
    }

    atualizarFiltros(clinicaId, data, medicoId, contexto)
    loading.value = true

    try {
      const raw = await listarAgendamentos({ clinicaId, data, medicoId, contexto })
      if (requestId !== fetchRequestId) return 'cancelled'

      if (raw.every(a => 'paciente' in a)) {
        agendamentos.value = (raw as AgendamentoComPaciente[]).map(item => ({ ...item, horario: normalizarHorario(item.horario) }))
        marcarContextoCarregado(clinicaId, data, medicoId, contexto)
        return 'success'
      }

      const allPacientes = await $fetch<Paciente[]>('/api/pacientes')
      if (requestId !== fetchRequestId) return 'cancelled'
      const pacienteMap = new Map(allPacientes.map(p => [p.id, p]))

      agendamentos.value = (raw as Agendamento[])
        .filter(a => pacienteMap.has(a.pacienteId))
        .map(a => ({
          ...a,
          horario: normalizarHorario(a.horario),
          paciente: pacienteMap.get(a.pacienteId)!
        }))
      marcarContextoCarregado(clinicaId, data, medicoId, contexto)
      return 'success'
    } catch {
      if (requestId !== fetchRequestId) return 'cancelled'
      console.error('Erro ao carregar agendamentos')
      return 'error'
    } finally {
      if (requestId === fetchRequestId) loading.value = false
    }
  }

  async function fetchAgendamentosExames(clinicaId?: number, data?: string) {
    atualizarFiltros(clinicaId, data)
    loading.value = true

    try {
      const raw = await listarAgendamentosExames({ clinicaId, data })
      agendamentos.value = raw.map(item => ({ ...item, horario: normalizarHorario(item.horario) }))
    } catch {
      console.error('Erro ao carregar agenda de exames')
    } finally {
      loading.value = false
    }
  }

  async function init(clinicaId?: number, data?: string, medicoId?: number, contexto?: AgendaContexto) {
    atualizarFiltros(clinicaId, data, medicoId, contexto)
    registrarSseHandlers()
    sse?.connect({ data, clinicaId, contexto })
    await fetchAgendamentos(clinicaId, data, medicoId, contexto)
  }

  async function initExames(clinicaId?: number, data?: string) {
    atualizarFiltros(clinicaId, data)
    registrarSseHandlers()
    sse?.connect({ data, clinicaId })
    await fetchAgendamentosExames(clinicaId, data)
  }

  async function atualizarStatus(id: number, status: AgendamentoStatus, consulta?: ConsultaStatusPayload, clinicaId?: number) {
    mutacoesStatusPendentes++
    fetchRequestId++
    atendimentoAtualRequestId++
    verificacaoAtendimentoAtual = null
    try {
      const chaveAtendimentoMutacao = atendimentoAtualChave
      const eraAtendimentoAtual = emAtendimento.value?.id === id
      const clinicaIdEfetiva = clinicaId
        ?? agendamentos.value.find(a => a.id === id)?.clinicaId
        ?? filtrosAtuais.clinicaId

      const atualizado = await atualizarStatusAgendamento(id, status, consulta, clinicaIdEfetiva)
      fetchRequestId++
      const completo = atualizado as AtualizarStatusAgendamentoResponse
      if (atendimentoAtualChave !== chaveAtendimentoMutacao) return atualizado
      if (clinicaCarregada.value && clinicaIdEfetiva && clinicaCarregada.value !== clinicaIdEfetiva) {
        return atualizado
      }
      aplicarStatusAgendamento(isAgendamentoComPaciente(completo) ? completo : { id, status })
      if (status === 'em-atendimento') {
        const atendimento = isAgendamentoComPaciente(completo)
          ? completo
          : agendamentos.value.find(item => item.id === id) ?? null
        marcarAtendimentoAtual(atendimento, chaveAtendimentoMutacao)
      } else if (eraAtendimentoAtual) {
        marcarAtendimentoAtual(null, chaveAtendimentoMutacao)
      }
      return atualizado
    } catch (error) {
      console.error('Erro ao atualizar status do agendamento')
      throw error
    } finally {
      mutacoesStatusPendentes--
      if (!mutacoesStatusPendentes) loading.value = false
    }
  }

  async function atualizarStatusExame(id: number, status: Extract<AgendamentoStatus, 'atendido' | 'faltou'>, clinicaId?: number) {
    try {
      const clinicaIdEfetiva = clinicaId
        ?? agendamentos.value.find(a => a.id === id)?.clinicaId
        ?? filtrosAtuais.clinicaId

      const atualizado = await atualizarStatusExameAgendamento(id, status, clinicaIdEfetiva)
      aplicarStatusAgendamento(atualizado)
      return atualizado
    } catch (error) {
      console.error('Erro ao atualizar status do exame')
      throw error
    }
  }

  return {
    agendamentos,
    loading,
    dataCarregada,
    clinicaCarregada,
    medicoCarregado,
    atendimentoAtualStatus,
    atendimentoAtualResumo,
    emAtendimento,
    fila,
    ordenados,
    totalAgendamentos,
    totalAtendidos,
    totalFaltas,
    init,
    initExames,
    fetchAgendamentos,
    fetchAgendamentosExames,
    verificarAtendimentoAtual,
    garantirAtendimentoAtual,
    invalidarAtendimentoAtual,
    atualizarStatusExame,
    atualizarStatus
  }
})
