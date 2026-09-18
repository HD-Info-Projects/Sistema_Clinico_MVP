import type { MedicoSpdata, RoleUsuario, Usuario, UsuarioForm } from '../types'

export type UsuarioResponse = {
  message?: string
  usuario?: Usuario
}

export function listarUsuarios(role?: RoleUsuario) {
  const query = role ? `?role=${role}` : ''
  return $fetch<Usuario[]>(`/api/usuarios${query}`)
}

export function criarUsuario(form: UsuarioForm) {
  return $fetch<UsuarioResponse>('/api/usuarios', {
    method: 'POST',
    body: form
  })
}

export function atualizarUsuario(id: number, form: Partial<UsuarioForm>) {
  return $fetch<UsuarioResponse>(`/api/usuarios/${id}`, {
    method: 'PUT',
    body: form
  })
}

export function excluirUsuario(id: number) {
  return $fetch<UsuarioResponse>(`/api/usuarios/${id}`, { method: 'DELETE' })
}

export function desbloquearUsuario(id: number) {
  return $fetch<UsuarioResponse>(`/api/usuarios/${id}/desbloquear`, { method: 'POST' })
}

export function buscarMedicosSpdataUsuarios(filtros: { spdata_id?: number | string, cpf?: string, nome?: string }) {
  const params = new URLSearchParams()
  if (filtros.spdata_id) params.set('spdata_id', String(filtros.spdata_id))
  if (filtros.cpf) params.set('cpf', filtros.cpf)
  if (filtros.nome) params.set('nome', filtros.nome)

  return $fetch<MedicoSpdata[]>(`/api/usuarios/medicos-spdata?${params.toString()}`)
}
