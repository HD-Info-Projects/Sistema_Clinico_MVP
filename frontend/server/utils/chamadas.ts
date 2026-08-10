import { broadcastSse } from './sse'

type ChamadoStatus = 'chamando' | 'concluido' | 'cancelado'

type Chamado = {
  id: number
  clinicaId: number
  pacienteId: number
  pacienteNome: string
  dataChamada: string
  status: ChamadoStatus
  localAtendimento: string
  medicoResponsavel: string
}

type CriarChamadoPayload = Pick<Chamado, 'clinicaId' | 'pacienteId' | 'pacienteNome' | 'localAtendimento' | 'medicoResponsavel'>

const chamados: Chamado[] = []
const MAX_CHAMADOS = 100

export function chamadoPublico(chamado: Chamado | null) {
  if (!chamado) return null

  return {
    id: chamado.id,
    clinicaId: chamado.clinicaId,
    pacienteId: 0,
    pacienteNome: chamado.pacienteNome,
    dataChamada: chamado.dataChamada,
    status: chamado.status,
    localAtendimento: chamado.localAtendimento,
    medicoResponsavel: ''
  }
}

export function getChamadoAtivo(clinicaId: number) {
  return chamados.find(chamado => chamado.clinicaId === clinicaId && chamado.status === 'chamando') ?? null
}

export function getHistoricoChamados(clinicaId: number, limit = 10) {
  const safeLimit = Number.isFinite(limit) ? Math.min(Math.max(Math.trunc(limit), 1), 100) : 10

  return chamados
    .filter(chamado => chamado.clinicaId === clinicaId && chamado.status !== 'chamando')
    .slice()
    .reverse()
    .slice(0, safeLimit)
}

export function criarChamado(data: CriarChamadoPayload) {
  const chamadoAtivo = chamados.find(chamado => chamado.clinicaId === data.clinicaId && chamado.status === 'chamando')

  if (chamadoAtivo?.pacienteId === data.pacienteId) {
    chamadoAtivo.pacienteNome = data.pacienteNome
    chamadoAtivo.localAtendimento = data.localAtendimento
    chamadoAtivo.medicoResponsavel = data.medicoResponsavel
    chamadoAtivo.dataChamada = new Date().toLocaleTimeString('pt-BR')
    broadcastSse({ type: 'chamado:novo', data: chamadoAtivo }, data.clinicaId)

    return chamadoAtivo
  }

  for (const chamado of chamados) {
    if (chamado.clinicaId === data.clinicaId && chamado.status === 'chamando') {
      chamado.status = 'concluido'
      broadcastSse({ type: 'chamado:concluido', data: chamado }, data.clinicaId)
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
  broadcastSse({ type: 'chamado:novo', data: chamado }, data.clinicaId)

  return chamado
}

export function atualizarChamadoStatus(id: number, clinicaId: number, status: ChamadoStatus) {
  const chamado = chamados.find(chamado => chamado.id === id && chamado.clinicaId === clinicaId)
  if (!chamado) return null

  chamado.status = status
  broadcastSse({ type: 'chamado:concluido', data: chamado }, clinicaId)

  return chamado
}
