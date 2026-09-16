import type { Chamado, CriarChamadoPayload, GerarAudioChamadoOptions } from '../types'

function chamadasQuery(clinicaId?: number | null) {
  return clinicaId ? `?clinicaId=${encodeURIComponent(String(clinicaId))}` : ''
}

export function buscarChamadoAtivo(clinicaId?: number | null) {
  return $fetch<Chamado | null>(`/api/chamadas/ativa${chamadasQuery(clinicaId)}`)
}

export function listarHistoricoChamadas(clinicaId?: number | null) {
  return $fetch<Chamado[]>(`/api/chamadas/historico${chamadasQuery(clinicaId)}`)
}

export function criarChamado(payload: CriarChamadoPayload, clinicaId?: number | null) {
  return $fetch<Chamado>(`/api/chamadas${chamadasQuery(clinicaId)}`, {
    method: 'POST',
    body: { ...payload, clinicaId }
  })
}

export function concluirChamado(chamadoId: number, clinicaId?: number | null) {
  return $fetch<Chamado>(`/api/chamadas/${chamadoId}${chamadasQuery(clinicaId)}`, {
    method: 'PATCH',
    body: { status: 'concluido' }
  })
}

export function concluirChamadoPublico(chamadoId: number, clinicaId: number) {
  return $fetch<Chamado>('/api/chamadas/concluir', {
    method: 'POST',
    body: { chamadoId, clinicaId }
  })
}

export async function gerarAudioChamado(chamadoId: number, options: GerarAudioChamadoOptions = {}) {
  const res = await fetch('/api/tts/speak', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ chamadoId, voice: options.voice }),
    signal: options.signal
  })

  if (!res.ok) {
    let message = 'Erro ao gerar áudio'

    try {
      const body = (await res.json()) as {
        error?: string
        statusMessage?: string
        message?: string
      }
      message = body.statusMessage || body.message || body.error || message
    } catch {
      // Mantém a mensagem padrão quando a resposta não é JSON.
    }

    throw new Error(message)
  }

  return res.blob()
}
