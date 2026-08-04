import type { H3Event } from 'h3'
import { createError, getCookie, getHeader, getQuery } from 'h3'

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
  const raw = getHeader(event, 'x-unidade-id')
    || firstQueryValue(query.unidadeId)
    || firstQueryValue(query.clinicaId)
    || getCookie(event, 'active_clinica_id')

  if (raw === undefined || raw === null || String(raw).trim() === '') return null

  const id = Number(raw)
  if (!Number.isInteger(id) || id <= 0) {
    throw createError({ statusCode: 400, statusMessage: 'unidadeId inválido' })
  }

  return id
}

export function requireClinicaUsuario(event: H3Event, rawUser: BackendUserWithClinicas) {
  const clinicas = clinicasFromBackend(rawUser)
  const activeId = getActiveClinicaId(event)

  if (!activeId && clinicas.length === 1) return clinicas[0]!.id
  if (!activeId) throw createError({ statusCode: 400, statusMessage: 'Unidade ativa obrigatória' })

  if (!clinicas.some(c => c.id === activeId)) {
    throw createError({ statusCode: 403, statusMessage: 'Acesso negado à unidade' })
  }

  return activeId
}

export async function getClinicaPublica(id: string | number) {
  const config = useRuntimeConfig()
  return await $fetch<ServerClinica>(`${config.flaskBaseUrl}/unidades/${encodeURIComponent(String(id))}/publica`)
}
