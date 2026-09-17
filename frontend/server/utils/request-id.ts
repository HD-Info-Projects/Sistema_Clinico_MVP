import { randomUUID } from 'node:crypto'
import type { H3Event } from 'h3'
import { setResponseHeader } from 'h3'
import { fetchErrorStatus } from './proxy-error'

export const REQUEST_ID_HEADER = 'X-Request-ID'

type ErrorWithCode = {
  code?: unknown
  cause?: {
    code?: unknown
  }
}

export function getRequestId(event: H3Event) {
  const existing = event.context.requestId
  if (typeof existing === 'string' && existing) return existing

  const requestId = randomUUID()
  event.context.requestId = requestId
  setResponseHeader(event, REQUEST_ID_HEADER, requestId)
  return requestId
}

export function logUpstreamFailure(event: H3Event, error: unknown, upstream: string, operation: string) {
  const status = fetchErrorStatus(error)
  if (status && status < 500) return

  const fetchError = error as ErrorWithCode
  const rawCode = fetchError.cause?.code ?? fetchError.code
  const code = typeof rawCode === 'string' ? rawCode.slice(0, 64) : undefined

  console.error('[bff] Falha no upstream', {
    requestId: getRequestId(event),
    upstream,
    operation,
    status,
    code
  })
}
