type SseHandler = (data: unknown) => void
type SseConnectOptions = {
  data?: string
  clinicaId?: number | null
  public?: boolean
}

let eventSource: EventSource | null = null
let reconnectTimer: ReturnType<typeof setTimeout> | null = null
let currentUrl = ''

const handlers = new Map<string, Set<SseHandler>>()
const SSE_EVENTS = [
  'agenda:snapshot',
  'agenda:error',
  'agendamento:status',
  'paciente:status',
  'chamado:novo',
  'chamado:concluido'
]

function buildUrl(options?: SseConnectOptions) {
  const params = new URLSearchParams()
  if (options?.data) params.set('data', options.data)
  if (options?.clinicaId) params.set('clinicaId', String(options.clinicaId))

  const qs = params.toString()
  const path = options?.public ? '/api/sse/tv' : '/api/sse'
  return `${path}${qs ? `?${qs}` : ''}`
}

function clearReconnectTimer() {
  if (reconnectTimer) {
    clearTimeout(reconnectTimer)
    reconnectTimer = null
  }
}

function handleEvent(eventType: string, raw: string) {
  try {
    const data = JSON.parse(raw)
    handlers.get(eventType)?.forEach(h => h(data))
  } catch { /* ignore malformed */ }
}

let reconnectAttempts = 0
const MAX_RECONNECT_ATTEMPTS = 5

function openConnection(url: string) {
  clearReconnectTimer()

  eventSource = new EventSource(url)

  eventSource.onerror = () => {
    eventSource?.close()
    eventSource = null
    clearReconnectTimer()
    reconnectAttempts++
    if (reconnectAttempts > MAX_RECONNECT_ATTEMPTS) return
    const delay = Math.min(3000 * Math.pow(2, reconnectAttempts - 1), 60000)
    reconnectTimer = setTimeout(() => {
      if (currentUrl === url) openConnection(url)
    }, delay)
  }

  eventSource.onopen = () => {
    reconnectAttempts = 0
  }

  for (const eventName of SSE_EVENTS) {
    eventSource.addEventListener(eventName, (event) => {
      handleEvent(eventName, event.data)
    })
  }
}

function disconnectShared() {
  clearReconnectTimer()

  if (eventSource) {
    eventSource.close()
    eventSource = null
  }

  currentUrl = ''
}

function connectShared(options?: SseConnectOptions) {
  if (!import.meta.client) return

  const nextUrl = options ? buildUrl(options) : currentUrl || buildUrl()
  if (eventSource && eventSource.readyState !== EventSource.CLOSED && currentUrl === nextUrl) return

  disconnectShared()
  currentUrl = nextUrl
  openConnection(nextUrl)
}

export function useSse() {
  function on(event: string, handler: SseHandler) {
    if (!handlers.has(event)) {
      handlers.set(event, new Set())
    }
    handlers.get(event)!.add(handler)
  }

  function off(event: string, handler: SseHandler) {
    handlers.get(event)?.delete(handler)
  }

  function connect(options?: SseConnectOptions) {
    connectShared(options)
  }

  function disconnect() {
    disconnectShared()
  }

  return { on, off, connect, disconnect }
}
