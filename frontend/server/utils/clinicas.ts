import type { H3Event } from 'h3'
import { createError, deleteCookie, getCookie, getHeader, getQuery, setCookie } from 'h3'

export const ACTIVE_CLINICA_COOKIE_NAME = 'active_clinica_id'

export interface ServerClinica {
  id: number
  nome: string
  slug?: string
  endereco: string
  telefone: string
  codigoSpdataCentroCusto?: number | null
  codigoSpdataAgenda?: string | null
}

type BackendClinica = {
  id: number
  nome: string
  slug?: string | null
  endereco?: string | null
  telefone?: string | null
  codigoSpdataCentroCusto?: number | null
  codigoSpdataAgenda?: string | null
  codigo_spdata_centro_custo?: number | null
  codigo_spdata_agenda?: string | null
}

type BackendUserWithClinicas = {
  unidades?: BackendClinica[]
  clinicas?: BackendClinica[]
}

function firstQueryValue(value: unknown) {
  if (Array.isArray(value)) return value[0]
  return value
}

function parseClinicaId(raw: unknown) {
  if (raw === undefined || raw === null) return null

  const text = String(raw).trim()
  if (!text || ['undefined', 'null', 'nan'].includes(text.toLowerCase())) return null

  const id = Number(text)
  return Number.isInteger(id) && id > 0 ? id : null
}

function activeClinicaCookieMaxAgeSeconds() {
  const config = useRuntimeConfig()
  return Number(config.public.authCookieMaxAgeSeconds) || 60 * 60 * 24 * 7
}

function activeClinicaCookieOptions(maxAge = activeClinicaCookieMaxAgeSeconds()) {
  return {
    httpOnly: true,
    secure: process.env.NUXT_AUTH_COOKIE_SECURE === 'true',
    sameSite: 'strict' as const,
    path: '/',
    maxAge
  }
}

export function setActiveClinicaIdCookie(event: H3Event, id: number) {
  const clinicaId = requireValidClinicaId(id)
  setCookie(event, ACTIVE_CLINICA_COOKIE_NAME, String(clinicaId), activeClinicaCookieOptions())
}

export function clearActiveClinicaIdCookie(event: H3Event) {
  deleteCookie(event, ACTIVE_CLINICA_COOKIE_NAME, activeClinicaCookieOptions(0))
}

export function getActiveClinicaCookieId(event: H3Event) {
  const cookieUnidade = getCookie(event, ACTIVE_CLINICA_COOKIE_NAME)
  const idCookie = parseClinicaId(cookieUnidade)
  if (cookieUnidade && !idCookie) clearActiveClinicaIdCookie(event)

  return idCookie
}

function requireValidClinicaId(raw: unknown) {
  const id = parseClinicaId(raw)
  if (!id) {
    throw createError({ statusCode: 400, message: 'unidadeId inválido' })
  }

  return id
}

export function normalizarClinica(raw: BackendClinica): ServerClinica {
  return {
    id: Number(raw.id),
    nome: String(raw.nome || ''),
    slug: raw.slug || undefined,
    endereco: raw.endereco || '',
    telefone: raw.telefone || '',
    codigoSpdataCentroCusto: raw.codigoSpdataCentroCusto ?? raw.codigo_spdata_centro_custo ?? null,
    codigoSpdataAgenda: raw.codigoSpdataAgenda ?? raw.codigo_spdata_agenda ?? null
  }
}

export function clinicasFromBackend(raw: BackendUserWithClinicas) {
  const unidades = raw.unidades ?? raw.clinicas ?? []
  return unidades.map(normalizarClinica).filter(c => Number.isFinite(c.id))
}

export function getActiveClinicaId(event: H3Event) {
  const query = getQuery(event)
  const headerUnidade = getHeader(event, 'x-unidade-id')
  const queryUnidade = firstQueryValue(query.unidadeId)
  const queryClinica = firstQueryValue(query.clinicaId)

  if (headerUnidade !== undefined && String(headerUnidade).trim() !== '') return requireValidClinicaId(headerUnidade)
  if (queryUnidade !== undefined && queryUnidade !== null && String(queryUnidade).trim() !== '') return requireValidClinicaId(queryUnidade)
  if (queryClinica !== undefined && queryClinica !== null && String(queryClinica).trim() !== '') return requireValidClinicaId(queryClinica)

  return getActiveClinicaCookieId(event)
}

export function resolveActiveClinicaIdCookie(event: H3Event, clinicas: ServerClinica[]) {
  const activeId = getActiveClinicaCookieId(event)

  if (activeId && clinicas.some(c => c.id === activeId)) {
    setActiveClinicaIdCookie(event, activeId)
    return activeId
  }

  if (clinicas.length === 1) {
    const unica = clinicas[0]!.id
    setActiveClinicaIdCookie(event, unica)
    return unica
  }

  clearActiveClinicaIdCookie(event)
  return null
}

export function requireClinicaUsuario(event: H3Event, rawUser: BackendUserWithClinicas) {
  const clinicas = clinicasFromBackend(rawUser)
  const activeId = getActiveClinicaId(event)

  if (!activeId && clinicas.length === 1) return clinicas[0]!.id
  if (!activeId) throw createError({ statusCode: 400, message: 'Unidade ativa obrigatória' })

  if (!clinicas.some(c => c.id === activeId)) {
    throw createError({ statusCode: 403, message: 'Acesso negado à unidade' })
  }

  return activeId
}

export async function getClinicaPublica(id: string | number) {
  const config = useRuntimeConfig()
  return await $fetch<ServerClinica>(`${config.flaskBaseUrl}/unidades/${encodeURIComponent(String(id))}/publica`)
}
