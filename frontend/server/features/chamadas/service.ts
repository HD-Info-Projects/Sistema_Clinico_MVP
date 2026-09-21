import type { H3Event } from 'h3'
import { createError, getRequestIP, setHeader } from 'h3'
import { useRuntimeConfig } from '#imports'
import { broadcastSse } from '../../utils/sse'

export type ChamadoStatus = 'chamando' | 'concluido' | 'cancelado'

export type Chamado = {
  id: number
  clinicaId: number
  pacienteId: number
  pacienteNome: string
  dataChamada: string
  status: ChamadoStatus
  localAtendimento: string
  medicoResponsavel: string
}

export type CriarChamadoPayload = Pick<Chamado, 'clinicaId' | 'pacienteId' | 'pacienteNome' | 'localAtendimento' | 'medicoResponsavel'>

const chamados: Chamado[] = []
const MAX_CHAMADOS = 100
const RATE_LIMIT_WINDOW_MS = 60_000
const RATE_LIMIT_MAX = 30
const rateLimit = new Map<string, { count: number, resetAt: number }>()

function nomePublicoPaciente(nome: string) {
  return String(nome || '').trim().replace(/\s+/g, ' ') || 'Paciente'
}

function localPublico(local: string) {
  return String(local || '').trim().slice(0, 80) || 'sala de atendimento'
}

function medicoPublico(nome: string) {
  return String(nome || '').trim().slice(0, 80)
}

function checkRateLimit(key: string) {
  const now = Date.now()
  const current = rateLimit.get(key)

  if (!current || current.resetAt <= now) {
    rateLimit.set(key, { count: 1, resetAt: now + RATE_LIMIT_WINDOW_MS })
    return true
  }

  if (current.count >= RATE_LIMIT_MAX) return false

  current.count += 1
  return true
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
  return chamados.find(chamado => chamado.id === id) ?? null
}

export function textoChamadoParaTts(id: number) {
  const chamado = getChamadoPorId(id)
  if (!chamado) return null

  return `${nomePublicoPaciente(chamado.pacienteNome)}, por favor dirija-se à ${localPublico(chamado.localAtendimento)}`
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

export async function gerarAudioChamadoTts(event: H3Event, body: { chamadoId?: number, voice?: string }) {
  const config = useRuntimeConfig()
  if (!config.enableTts) {
    throw createError({ statusCode: 503, statusMessage: 'TTS desabilitado' })
  }

  const chamadoId = Number(body?.chamadoId)

  if (!Number.isFinite(chamadoId) || chamadoId <= 0) {
    throw createError({ statusCode: 400, statusMessage: 'chamadoId inválido' })
  }

  const text = textoChamadoParaTts(chamadoId)
  if (!text) {
    throw createError({ statusCode: 404, statusMessage: 'Chamado não encontrado' })
  }

  const ip = getRequestIP(event) || 'unknown'
  if (!checkRateLimit(ip)) {
    throw createError({ statusCode: 429, statusMessage: 'Muitas solicitações de áudio' })
  }

  const res = await fetch(`${config.flaskBaseUrl}/tts/speak`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ text, voice: body?.voice, chamadoId })
  })

  if (!res.ok) {
    let message = 'Erro ao gerar áudio TTS'

    try {
      const errorBody = await res.json() as { error?: unknown }
      if (typeof errorBody.error === 'string' && errorBody.error) {
        message = errorBody.error
      }
    } catch {
      // Mantém mensagem genérica se o Flask não retornar JSON.
    }

    console.error('[tts] Falha ao gerar áudio no Flask', { status: res.status })

    throw createError({ statusCode: res.status, statusMessage: message })
  }

  const audio = await res.arrayBuffer()

  setHeader(event, 'Content-Type', 'audio/mpeg')
  setHeader(event, 'Cache-Control', 'no-store')

  return new Uint8Array(audio)
}
