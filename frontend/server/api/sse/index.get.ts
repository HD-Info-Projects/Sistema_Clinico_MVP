const POLL_INTERVAL_MS = 10000
const KEEP_ALIVE_MS = 15000

function hojeISO() {
  const data = new Date()
  data.setMinutes(data.getMinutes() - data.getTimezoneOffset())
  return data.toISOString().slice(0, 10)
}

export default defineEventHandler(async (event) => {
  const { req, res } = event.node
  const query = getQuery(event)
  const token = requireAuthToken(event)
  const authUser = await getAuthenticatedUser(event)
  const clinicaId = requireClinicaUsuario(event, authUser)
  const config = useRuntimeConfig()
  const dataParam = Array.isArray(query.data) ? query.data[0] : query.data
  const pollAgenda = Boolean(dataParam) && authUser.role === 'medico'
  const data = String(dataParam || hojeISO())

  res.writeHead(200, {
    'Content-Type': 'text/event-stream',
    'Cache-Control': 'no-cache, no-transform',
    'Connection': 'keep-alive',
    'X-Accel-Buffering': 'no'
  })
  res.flushHeaders?.()

  let closed = false
  let lastHash = ''
  let loadingAgenda = false

  function write(data: string) {
    if (closed) return
    try {
      res.write(data)
    } catch {
      closed = true
    }
  }

  function send(type: string, payload: unknown) {
    write(`event: ${type}\ndata: ${JSON.stringify(payload)}\n\n`)
  }

  async function carregarAgenda() {
    if (!pollAgenda || !token || closed || loadingAgenda) return

    loadingAgenda = true

    try {
      const items = await $fetch<unknown[]>(`${config.flaskBaseUrl}/agenda-medica/?data=${encodeURIComponent(data)}`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'X-Unidade-Id': String(clinicaId)
        }
      })

      const hash = JSON.stringify(items)
      if (hash !== lastHash) {
        lastHash = hash
        send('agenda:snapshot', { data, items })
      }
    } catch {
      send('agenda:error', { message: 'Falha ao atualizar agenda médica' })
    } finally {
      loadingAgenda = false
    }
  }

  send('connected', { ok: true })

  let poll: ReturnType<typeof setInterval> | null = null
  if (pollAgenda) {
    void carregarAgenda()
    poll = setInterval(() => {
      void carregarAgenda()
    }, POLL_INTERVAL_MS)
  }

  const keepAlive = setInterval(() => {
    write(':keepalive\n\n')
  }, KEEP_ALIVE_MS)

  const remove = addSseClient({
    write,
    close: () => {
      closed = true
      if (poll) clearInterval(poll)
      clearInterval(keepAlive)
      res.end()
    }
  }, `internal:${clinicaId}`)

  req.on('close', () => {
    closed = true
    if (poll) clearInterval(poll)
    clearInterval(keepAlive)
    remove()
  })

  // Prevent nitro from ending the response
  return new Promise(() => {})
})
