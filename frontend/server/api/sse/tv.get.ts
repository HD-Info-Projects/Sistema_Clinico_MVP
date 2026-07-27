const KEEP_ALIVE_MS = 15000

export default defineEventHandler((event) => {
  const { req, res } = event.node

  res.writeHead(200, {
    'Content-Type': 'text/event-stream',
    'Cache-Control': 'no-cache, no-transform',
    'Connection': 'keep-alive',
    'X-Accel-Buffering': 'no'
  })
  res.flushHeaders?.()

  let closed = false

  function write(data: string) {
    if (closed) return
    try {
      res.write(data)
    } catch {
      closed = true
    }
  }

  write(`event: connected\ndata: ${JSON.stringify({ ok: true, public: true })}\n\n`)

  const keepAlive = setInterval(() => {
    write(':keepalive\n\n')
  }, KEEP_ALIVE_MS)

  const remove = addSseClient({
    write,
    close: () => {
      closed = true
      clearInterval(keepAlive)
      res.end()
    }
  }, 'tv')

  req.on('close', () => {
    closed = true
    clearInterval(keepAlive)
    remove()
  })

  return new Promise(() => {})
})
