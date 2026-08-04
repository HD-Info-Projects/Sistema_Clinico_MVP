type SseClient = { write: (data: string) => void, close: () => void }
type SseChannel = 'internal' | 'tv'

const sseClients: Record<SseChannel, Set<SseClient>> = {
  internal: new Set(),
  tv: new Set()
}

function publicEventData(type: string, data: unknown) {
  if (!type.startsWith('chamado:') || !data || typeof data !== 'object') return data

  const chamado = data as Record<string, unknown>
  const pacienteNome = String(chamado.pacienteNome || '').trim().split(/\s+/)[0] || 'Paciente'
  return {
    id: chamado.id,
    pacienteId: 0,
    pacienteNome,
    dataChamada: chamado.dataChamada,
    status: chamado.status,
    localAtendimento: String(chamado.localAtendimento || '').trim().slice(0, 80),
    medicoResponsavel: ''
  }
}

function sendTo(channel: SseChannel, event: { type: string, data: unknown }) {
  const message = `event: ${event.type}\ndata: ${JSON.stringify(event.data)}\n\n`
  for (const client of [...sseClients[channel]]) {
    try {
      client.write(message)
    } catch {
      sseClients[channel].delete(client)
    }
  }
}

export function addSseClient(client: SseClient, channel: SseChannel = 'internal') {
  sseClients[channel].add(client)
  return () => {
    sseClients[channel].delete(client)
  }
}

export function broadcastSse(event: { type: string, data: unknown }) {
  sendTo('internal', event)
  if (event.type.startsWith('chamado:')) {
    sendTo('tv', { ...event, data: publicEventData(event.type, event.data) })
  }
}
