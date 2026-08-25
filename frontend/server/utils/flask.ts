/* eslint-disable @typescript-eslint/no-explicit-any */
import type { H3Event } from 'h3'

export function medicoAlvoParams(event: H3Event): Record<string, number> {
  const bruto = getQuery(event).medicoId ?? getQuery(event).medico_id
  if (bruto === undefined || bruto === null || String(bruto) === '') return {}
  const numero = Number(bruto)
  if (Number.isNaN(numero) || numero <= 0) return {}
  return { medico_id: numero }
}

export async function flaskFetch<T>(event: H3Event, path: string, opts?: any): Promise<T> {
  const token = requireAuthToken(event)
  const config = useRuntimeConfig()
  const { activeClinica = true, ...fetchOpts } = opts ?? {}
  const activeClinicaId = activeClinica ? getActiveClinicaId(event) : null

  return $fetch<T>(`${config.flaskBaseUrl}${path}`, {
    ...fetchOpts,
    headers: {
      ...fetchOpts.headers,
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(activeClinicaId ? { 'X-Unidade-Id': String(activeClinicaId) } : {})
    }
  }) as T
}
