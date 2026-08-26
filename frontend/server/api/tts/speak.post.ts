import { getRequestIP, readBody } from 'h3'

const RATE_LIMIT_WINDOW_MS = 60_000
const RATE_LIMIT_MAX = 30
const rateLimit = new Map<string, { count: number, resetAt: number }>()

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

export default defineEventHandler(async (event) => {
  const config = useRuntimeConfig()
  if (!config.enableTts) {
    throw createError({ statusCode: 503, statusMessage: 'TTS desabilitado' })
  }

  const body = await readBody<{ chamadoId?: number, voice?: string }>(event)
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
})
