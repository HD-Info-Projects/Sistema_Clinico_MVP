/* eslint-disable @typescript-eslint/no-explicit-any */
import type { H3Event } from 'h3'

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
