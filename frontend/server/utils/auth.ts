import type { H3Event } from 'h3'
import { createError, deleteCookie, getCookie, setCookie } from 'h3'
import type { ServerClinica } from './clinicas'
import { clearActiveClinicaIdCookie, clinicasFromBackend, resolveActiveClinicaIdCookie, setActiveClinicaIdCookie } from './clinicas'

export const AUTH_COOKIE_NAME = 'auth_token'

type BackendAuthUser = {
  id: number
  email: string
  nome_completo: string
  role: 'medico' | 'recepcao' | 'admin' | 'dpo' | 'ti'
  crm?: string | null
  especialidade?: string | null
  unidades?: ServerClinica[]
  clinicas?: ServerClinica[]
}

function authCookieMaxAgeSeconds() {
  const config = useRuntimeConfig()
  const maxAge = Number(config.public.authCookieMaxAgeSeconds) || 60 * 60 * 24 * 7
  return maxAge
}

function authCookieOptions(maxAge = authCookieMaxAgeSeconds()) {
  return {
    httpOnly: true,
    secure: process.env.NUXT_AUTH_COOKIE_SECURE === 'true',
    sameSite: 'strict' as const,
    path: '/',
    maxAge
  }
}

export function setAuthTokenCookie(event: H3Event, token: string) {
  setCookie(event, AUTH_COOKIE_NAME, token, authCookieOptions())
}

export function clearAuthTokenCookie(event: H3Event) {
  deleteCookie(event, AUTH_COOKIE_NAME, authCookieOptions(0))
}

export function requireAuthToken(event: H3Event) {
  const token = getCookie(event, AUTH_COOKIE_NAME)

  if (!token) {
    throw createError({ statusCode: 401, statusMessage: 'Não autorizado' })
  }

  return token
}

function buildAuthPayloadFromClinicas(raw: BackendAuthUser, clinicas: ServerClinica[], activeClinicaId: number | null) {
  const clinicaIds = clinicas.map(c => c.id)

  return {
    user: {
      id: raw.id,
      nome: raw.nome_completo,
      email: raw.email,
      role: raw.role,
      crm: raw.crm ?? undefined,
      especialidades: raw.especialidade ? [raw.especialidade] : [],
      clinicaIds
    },
    clinicas,
    activeClinicaId
  }
}

export function buildAuthPayload(raw: BackendAuthUser, activeClinicaId: number | null = null) {
  return buildAuthPayloadFromClinicas(raw, clinicasFromBackend(raw), activeClinicaId)
}

export function buildAuthSessionPayload(event: H3Event, raw: BackendAuthUser) {
  const clinicas = clinicasFromBackend(raw)
  const activeClinicaId = resolveActiveClinicaIdCookie(event, clinicas)

  return buildAuthPayloadFromClinicas(raw, clinicas, activeClinicaId)
}

export function buildLoginSessionPayload(event: H3Event, raw: BackendAuthUser) {
  const clinicas = clinicasFromBackend(raw)
  const activeClinicaId = clinicas.length === 1 ? clinicas[0]!.id : null

  if (activeClinicaId) {
    setActiveClinicaIdCookie(event, activeClinicaId)
  } else {
    clearActiveClinicaIdCookie(event)
  }

  return buildAuthPayloadFromClinicas(raw, clinicas, activeClinicaId)
}

export async function getAuthenticatedUser(event: H3Event) {
  const token = requireAuthToken(event)
  const config = useRuntimeConfig()

  try {
    return await $fetch<BackendAuthUser>(`${config.flaskBaseUrl}/login/me`, {
      headers: {
        Authorization: `Bearer ${token}`
      }
    })
  } catch {
    clearAuthTokenCookie(event)
    clearActiveClinicaIdCookie(event)
    throw createError({ statusCode: 401, statusMessage: 'Não autorizado' })
  }
}

export async function requireRole(event: H3Event, roles: BackendAuthUser['role'][]) {
  const user = await getAuthenticatedUser(event)

  if (!roles.includes(user.role)) {
    throw createError({ statusCode: 403, statusMessage: 'Acesso negado' })
  }

  return user
}
