import { broadcastSse } from './sse'

type ChamadoStatus = 'chamando' | 'concluido' | 'cancelado'

type Chamado = {
  id: number
  pacienteId: number
  pacienteNome: string
  dataChamada: string
  status: ChamadoStatus
  localAtendimento: string
  medicoResponsavel: string
}

type CriarChamadoPayload = Pick<Chamado, 'pacienteId' | 'pacienteNome' | 'localAtendimento' | 'medicoResponsavel'>

const chamados: Chamado[] = []
const MAX_CHAMADOS = 100

function nomePublicoPaciente(nome: string) {
  const primeiroNome = String(nome || '').trim().split(/\s+/)[0]
  return primeiroNome || 'Paciente'
}

function localPublico(local: string) {
  return String(local || '').trim().slice(0, 80) || 'sala de atendimento'
}

export function chamadoPublico(chamado: Chamado | null) {
  if (!chamado) return null

  return {
    id: chamado.id,
    pacienteId: 0,
    pacienteNome: nomePublicoPaciente(chamado.pacienteNome),
    dataChamada: chamado.dataChamada,
    status: chamado.status,
    localAtendimento: localPublico(chamado.localAtendimento),
    medicoResponsavel: ''
  }
}

export function getChamadoPorId(id: number) {
  return chamados.find(chamado => chamado.id === id) ?? null
}

export function textoChamadoParaTts(id: number) {
  const chamado = getChamadoPorId(id)
  if (!chamado) return null

  return `${nomePublicoPaciente(chamado.pacienteNome)}, por favor dirija-se à ${localPublico(chamado.localAtendimento)}`
}

export function getChamadoAtivo() {
  return chamados.find(chamado => chamado.status === 'chamando') ?? null
}

export function getHistoricoChamados(limit = 10) {
  const safeLimit = Number.isFinite(limit) ? Math.min(Math.max(Math.trunc(limit), 1), 100) : 10

  return chamados
    .filter(chamado => chamado.status !== 'chamando')
    .slice()
    .reverse()
    .slice(0, safeLimit)
}

export function criarChamado(data: CriarChamadoPayload) {
  const chamadoAtivo = chamados.find(chamado => chamado.status === 'chamando')

  if (chamadoAtivo?.pacienteId === data.pacienteId) {
    chamadoAtivo.pacienteNome = data.pacienteNome
    chamadoAtivo.localAtendimento = data.localAtendimento
    chamadoAtivo.medicoResponsavel = data.medicoResponsavel
    chamadoAtivo.dataChamada = new Date().toLocaleTimeString('pt-BR')
    broadcastSse({ type: 'chamado:novo', data: chamadoAtivo })

    return chamadoAtivo
  }

  for (const chamado of chamados) {
    if (chamado.status === 'chamando') {
      chamado.status = 'concluido'
      broadcastSse({ type: 'chamado:concluido', data: chamado })
    }
  }

  const chamado: Chamado = {
    id: Date.now(),
    ...data,
    dataChamada: new Date().toLocaleTimeString('pt-BR'),
    status: 'chamando'
  }

  chamados.push(chamado)
  if (chamados.length > MAX_CHAMADOS) {
    chamados.splice(0, chamados.length - MAX_CHAMADOS)
  }
  broadcastSse({ type: 'chamado:novo', data: chamado })

  return chamado
}

export function atualizarChamadoStatus(id: number, status: ChamadoStatus) {
  const chamado = chamados.find(chamado => chamado.id === id)
  if (!chamado) return null

  chamado.status = status
  broadcastSse({ type: 'chamado:concluido', data: chamado })

  return chamado
}
