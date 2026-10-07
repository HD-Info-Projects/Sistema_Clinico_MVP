import type { H3Event } from 'h3'
import { getHeader, getRequestIP } from 'h3'

export const CLIENT_PUBLIC_IP_HEADER = 'X-Client-Public-IP'

function headerString(valor: string | string[] | undefined) {
  if (Array.isArray(valor)) return valor[0]
  return valor
}

export function getClientPublicIp(event: H3Event) {
  return headerString(getHeader(event, 'cf-connecting-ip'))
    || headerString(getHeader(event, 'x-real-ip'))
    || getRequestIP(event, { xForwardedFor: true })
    || event.node.req.socket.remoteAddress
    || undefined
}

export function forwardedClientHeaders(event: H3Event) {
  const clientIp = getClientPublicIp(event)
  const headers: Record<string, string> = {}

  if (!clientIp) return headers

  const forwardedFor = headerString(getHeader(event, 'x-forwarded-for'))
  headers[CLIENT_PUBLIC_IP_HEADER] = clientIp
  headers['X-Forwarded-For'] = forwardedFor ? `${forwardedFor}, ${clientIp}` : clientIp
  headers['X-Real-IP'] = clientIp

  return headers
}
