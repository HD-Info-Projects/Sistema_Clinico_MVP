import type { H3Event } from 'h3'
import { flaskFetch } from '../../utils/flask'
import type { AtualizarUsuarioBody, CriarUsuarioBody } from './schema'

export function listarUsuarios(event: H3Event, role?: string) {
  const params = new URLSearchParams()
  if (role) params.set('role', role)

  return flaskFetch(event, `/usuarios${params.toString() ? `?${params.toString()}` : ''}`)
}

export function criarUsuario(event: H3Event, body: CriarUsuarioBody) {
  return flaskFetch(event, '/usuarios', {
    method: 'POST',
    body
  })
}

export function atualizarUsuario(event: H3Event, id: string, body: AtualizarUsuarioBody) {
  return flaskFetch(event, `/usuarios/${id}`, {
    method: 'PUT',
    body
  })
}

export function excluirUsuario(event: H3Event, id: string) {
  return flaskFetch(event, `/usuarios/${id}`, { method: 'DELETE' })
}

export function buscarMedicosSpdata(event: H3Event, query: Record<string, unknown>) {
  const params = new URLSearchParams()

  for (const key of ['spdata_id', 'cpf', 'nome']) {
    if (query[key]) params.set(key, String(query[key]))
  }

  return flaskFetch(event, `/usuarios/medicos-spdata${params.toString() ? `?${params.toString()}` : ''}`)
}
