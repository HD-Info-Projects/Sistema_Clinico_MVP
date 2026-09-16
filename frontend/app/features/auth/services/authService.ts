import type { AuthSessionResponse } from '../types'

export function loginAuth(credentials: Record<string, unknown>) {
  return $fetch<AuthSessionResponse>('/api/auth/login', {
    method: 'POST',
    body: credentials
  })
}

export function logoutAuth() {
  return $fetch('/api/auth/logout', { method: 'POST' })
}

export function buscarSessaoAuth() {
  return $fetch<AuthSessionResponse>('/api/auth/me')
}
