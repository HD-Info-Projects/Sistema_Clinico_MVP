import type { H3Event } from 'h3'
import { setResponseHeader } from 'h3'

export function setPrivateNoStore(event: H3Event) {
  setResponseHeader(event, 'Cache-Control', 'no-store, private')
  setResponseHeader(event, 'Pragma', 'no-cache')
  setResponseHeader(event, 'X-Content-Type-Options', 'nosniff')
}
