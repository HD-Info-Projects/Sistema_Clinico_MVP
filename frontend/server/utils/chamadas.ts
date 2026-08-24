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
const clinicasComChamadas = new Set<number>()
const MAX_CHAMADOS = 100

let dataAtualChamadas = dataLocalAtual()
let resetTimer: ReturnType<typeof setTimeout> | null = null

function dataLocalAtual(data = new Date()) {
  const ano = data.getFullYear()
  const mes = String(data.getMonth() + 1).padStart(2, '0')
  const dia = String(data.getDate()).padStart(2, '0')

  return `${ano}-${mes}-${dia}`
}

function milissegundosAteProximaMeiaNoite(data = new Date()) {
  const proximaMeiaNoite = new Date(data)
  proximaMeiaNoite.setDate(proximaMeiaNoite.getDate() + 1)
  proximaMeiaNoite.setHours(0, 0, 1, 0)

  return Math.max(proximaMeiaNoite.getTime() - data.getTime(), 1000)
}

function registrarClinica(clinicaId: number) {
  if (Number.isInteger(clinicaId) && clinicaId > 0) clinicasComChamadas.add(clinicaId)
}

function clinicasParaReset() {
  for (const chamado of chamados) registrarClinica(chamado.clinicaId)
  return Array.from(clinicasComChamadas)
}

function resetarChamadosSeNecessario() {
  const hoje = dataLocalAtual()
  if (hoje === dataAtualChamadas) return

  const clinicaIds = clinicasParaReset()
  chamados.splice(0, chamados.length)
  dataAtualChamadas = hoje

  for (const clinicaId of clinicaIds) {
    broadcastSse({ type: 'chamado:reset', data: { clinicaId, data: hoje } }, clinicaId)
  }
}

function prepararClinica(clinicaId: number) {
  registrarClinica(clinicaId)
  resetarChamadosSeNecessario()
}

function agendarResetDiario() {
  if (resetTimer) clearTimeout(resetTimer)

  resetTimer = setTimeout(() => {
    resetarChamadosSeNecessario()
    agendarResetDiario()
  }, milissegundosAteProximaMeiaNoite())

  if (typeof resetTimer === 'object' && resetTimer && 'unref' in resetTimer) {
    (resetTimer as { unref: () => void }).unref()
  }
}

agendarResetDiario()

function nomePublicoPaciente(nome: string) {
  const primeiroNome = String(nome || '').trim().split(/\s+/)[0]
  return primeiroNome || 'Paciente'
}

function localPublico(local: string) {
  return String(local || '').trim().slice(0, 80) || 'sala de atendimento'
}

function medicoPublico(nome: string) {
  return String(nome || '').trim().slice(0, 80)
}

export function chamadoPublico(chamado: Chamado | null) {
  if (!chamado) return null

  return {
    id: chamado.id,
    clinicaId: chamado.clinicaId,
    pacienteId: 0,
    pacienteNome: nomePublicoPaciente(chamado.pacienteNome),
    dataChamada: chamado.dataChamada,
    status: chamado.status,
    localAtendimento: localPublico(chamado.localAtendimento),
    medicoResponsavel: medicoPublico(chamado.medicoResponsavel)
  }
}

export function getChamadoPorId(id: number) {
  resetarChamadosSeNecessario()
  return chamados.find(chamado => chamado.id === id) ?? null
}

export function textoChamadoParaTts(id: number) {
  const chamado = getChamadoPorId(id)
  if (!chamado) return null

  return `${nomePublicoPaciente(chamado.pacienteNome)}, por favor dirija-se à ${localPublico(chamado.localAtendimento)}`
}

export function getChamadoAtivo(clinicaId: number) {
  prepararClinica(clinicaId)
  return chamados.find(chamado => chamado.clinicaId === clinicaId && chamado.status === 'chamando') ?? null
}

export function getHistoricoChamados(clinicaId: number, limit = 10) {
  prepararClinica(clinicaId)
  const safeLimit = Number.isFinite(limit) ? Math.min(Math.max(Math.trunc(limit), 1), 100) : 10

  return chamados
    .filter(chamado => chamado.clinicaId === clinicaId && chamado.status !== 'chamando')
    .slice()
    .reverse()
    .slice(0, safeLimit)
}

export function criarChamado(data: CriarChamadoPayload) {
  prepararClinica(data.clinicaId)
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
  prepararClinica(clinicaId)
  const chamado = chamados.find(chamado => chamado.id === id && chamado.clinicaId === clinicaId)
  if (!chamado) return null

  chamado.status = status
  broadcastSse({ type: 'chamado:concluido', data: chamado }, clinicaId)

  return chamado
}
