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

const SAFE_MESSAGE_STATUS = new Set([400, 401, 403, 404, 409, 422, 429])

export function fetchErrorStatus(error: unknown) {
  const fetchError = error as FetchErrorLike
  return fetchError.response?.status
    || fetchError.statusCode
    || fetchError.status
}

export function throwProxyError(error: unknown, fallback: string): never {
  const fetchError = error as FetchErrorLike
  const data = fetchError.data || fetchError.response?._data
  const statusCode = fetchErrorStatus(error) || 502
  const upstreamMessage = data?.error
    || data?.message
    || data?.statusMessage
    || fetchError.statusMessage
  const message = SAFE_MESSAGE_STATUS.has(statusCode) && upstreamMessage
    ? upstreamMessage
    : fallback

  throw createError({
    statusCode,
    statusMessage: message,
    data: { message }
  })
}
