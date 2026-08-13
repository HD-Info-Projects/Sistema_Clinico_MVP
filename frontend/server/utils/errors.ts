import { createError } from 'h3'

type ProxyErrorData = {
  error?: string
  message?: string
  statusMessage?: string
}

type ProxyFetchError = {
  status?: number
  statusCode?: number
  response?: { status?: number, _data?: ProxyErrorData }
  data?: ProxyErrorData
  message?: string
}

export function proxyErrorMessage(error: unknown, fallback: string) {
  const fetchError = error as ProxyFetchError
  const data = fetchError.response?._data ?? fetchError.data

  return data?.error
    || data?.message
    || data?.statusMessage
    || fetchError.message
    || fallback
}

export function throwProxyError(error: unknown, fallbackMessage: string, fallbackStatusCode = 502): never {
  const fetchError = error as ProxyFetchError
  const data = fetchError.response?._data ?? fetchError.data
  const statusCode = fetchError.response?.status
    ?? fetchError.statusCode
    ?? fetchError.status
    ?? fallbackStatusCode

  throw createError({
    statusCode,
    message: proxyErrorMessage(error, fallbackMessage),
    data: data ?? String(error)
  })
}
