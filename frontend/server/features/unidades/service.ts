import type { H3Event } from 'h3'
import { flaskFetch } from '../../utils/flask'

export function listarUnidades(event: H3Event) {
  return flaskFetch(event, '/unidades')
}

export function criarUnidade(event: H3Event, body: unknown) {
  return flaskFetch(event, '/unidades', {
    method: 'POST',
    body
  })
}

export function atualizarUnidade(event: H3Event, id: string, body: unknown) {
  return flaskFetch(event, `/unidades/${id}`, {
    method: 'PUT',
    body
  })
}

export function excluirUnidade(event: H3Event, id: string) {
  return flaskFetch(event, `/unidades/${id}`, { method: 'DELETE' })
}
