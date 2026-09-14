import type { H3Event } from 'h3'
import { flaskFetch } from '../../utils/flask'

export function buscarProcedimentos(event: H3Event, q?: string) {
  const endpoint = q && q.length >= 2
    ? `/procedimentos/buscar?q=${encodeURIComponent(q)}`
    : '/procedimentos/buscar'

  return flaskFetch(event, endpoint, { activeClinica: false })
}
