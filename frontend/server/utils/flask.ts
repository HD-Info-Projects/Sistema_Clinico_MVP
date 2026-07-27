/* eslint-disable @typescript-eslint/no-explicit-any */
import type { H3Event } from 'h3'

export async function flaskFetch<T>(event: H3Event, path: string, opts?: any): Promise<T> {
  const token = requireAuthToken(event)
  const config = useRuntimeConfig()

  return $fetch<T>(`${config.flaskBaseUrl}${path}`, {
    ...opts,
    headers: {
      ...opts?.headers,
      ...(token ? { Authorization: `Bearer ${token}` } : {})
    }
  }) as T
}
