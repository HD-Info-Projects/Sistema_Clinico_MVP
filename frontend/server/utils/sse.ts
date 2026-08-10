type SseClient = { write: (data: string) => void, close: () => void }
type SseChannel = string

const sseClients = new Map<SseChannel, Set<SseClient>>()

function clientsFor(channel: SseChannel) {
  if (!sseClients.has(channel)) {
    sseClients.set(channel, new Set())
  }
  return sseClients.get(channel)!
}

function publicEventData(type: string, data: unknown) {
  if (!type.startsWith('chamado:') || !data || typeof data !== 'object') return data

  const chamado = data as Record<string, unknown>
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

function sendTo(channel: SseChannel, event: { type: string, data: unknown }) {
  const clients = clientsFor(channel)
  const message = `event: ${event.type}\ndata: ${JSON.stringify(event.data)}\n\n`
  for (const client of [...clients]) {
    try {
      client.write(message)
    } catch {
      clients.delete(client)
    }
  }
}

export function addSseClient(client: SseClient, channel: SseChannel) {
  clientsFor(channel).add(client)
  return () => {
    clientsFor(channel).delete(client)
  }
}

export function broadcastSse(event: { type: string, data: unknown }, clinicaId?: number | null) {
  if (!clinicaId) {
    sendTo('internal', event)
    if (event.type.startsWith('chamado:')) {
      sendTo('tv', { ...event, data: publicEventData(event.type, event.data) })
    }
    return
  }

  sendTo(`internal:${clinicaId}`, event)
  if (event.type.startsWith('chamado:')) {
    sendTo(`tv:${clinicaId}`, { ...event, data: publicEventData(event.type, event.data) })
  }
}
