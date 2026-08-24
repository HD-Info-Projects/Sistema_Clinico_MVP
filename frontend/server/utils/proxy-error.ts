import { createError } from 'h3'

type FetchErrorLike = {
  status?: number
  statusCode?: number
  statusMessage?: string
  message?: string
  data?: {
    error?: string
    message?: string
    statusMessage?: string
  }
  response?: {
    status?: number
    _data?: {
      error?: string
      message?: string
      statusMessage?: string
    }
  }
}

export function throwProxyError(error: unknown, fallback: string): never {
  const fetchError = error as FetchErrorLike
  const data = fetchError.data || fetchError.response?._data
  const message = data?.error
    || data?.message
    || data?.statusMessage
    || fetchError.statusMessage
    || fallback
  const statusCode = fetchError.response?.status
    || fetchError.statusCode
    || fetchError.status
    || 500

  throw createError({
    statusCode,
    statusMessage: message,
    data: { message }
  })
}
