import type { H3Event } from 'h3'
import { fetchErrorStatus } from '../../utils/proxy-error'
import { getRequestId, logUpstreamFailure, REQUEST_ID_HEADER } from '../../utils/request-id'
import { setPrivateNoStore } from '../../utils/response'

export async function loginAuth(event: H3Event, body: { username?: string, password?: string }) {
  setPrivateNoStore(event)
  const { username, password } = body
  const config = useRuntimeConfig()
  const requestId = getRequestId(event)

  let res: { access_token?: string }
  try {
    res = await $fetch(`${config.flaskBaseUrl}/login/auth`, {
      method: 'POST',
      headers: { [REQUEST_ID_HEADER]: requestId },
      body: { username, senha: password }
    })
  } catch (error: unknown) {
    const status = fetchErrorStatus(error)

    if (status === 400 || status === 401 || status === 423 || status === 429) {
      throw createError({
        statusCode: status,
        statusMessage: status === 429
          ? 'Muitas tentativas de login. Aguarde 60 segundos e tente novamente.'
          : status === 423
            ? 'Conta bloqueada. Solicite o desbloqueio ao administrador.'
            : 'Credenciais inválidas'
      })
    }

    logUpstreamFailure(event, error, 'flask', 'autenticar')
    throw createError({
      statusCode: 502,
      statusMessage: 'Falha ao conectar com o backend Flask'
    })
  }

  if (!res.access_token) {
    throw createError({ statusCode: 401, statusMessage: 'Credenciais inválidas' })
  }

  try {
    const rawUser = await $fetch(`${config.flaskBaseUrl}/login/me`, {
      headers: {
        Authorization: `Bearer ${res.access_token}`,
        [REQUEST_ID_HEADER]: requestId
      }
    })

    setAuthTokenCookie(event, res.access_token)
    return buildLoginSessionPayload(event, rawUser as Parameters<typeof buildLoginSessionPayload>[1])
  } catch (error: unknown) {
    const status = fetchErrorStatus(error)
    logUpstreamFailure(event, error, 'flask', 'validar nova sessão')
    if (status === 401 || status === 403) {
      throw createError({ statusCode: 401, statusMessage: 'Credenciais inválidas' })
    }
    throw createError({ statusCode: 502, statusMessage: 'Falha ao carregar sessão' })
  }
}

export async function buscarSessaoAuth(event: H3Event) {
  setPrivateNoStore(event)
  const rawUser = await getAuthenticatedUser(event)
  return buildAuthSessionPayload(event, rawUser)
}

export async function logoutAuth(event: H3Event) {
  setPrivateNoStore(event)
  const requestId = getRequestId(event)
  const token = getCookie(event, AUTH_COOKIE_NAME)
  if (token) {
    const config = useRuntimeConfig()
    try {
      await $fetch(`${config.flaskBaseUrl}/login/logout`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${token}`,
          [REQUEST_ID_HEADER]: requestId
        }
      })
    } catch (error) {
      logUpstreamFailure(event, error, 'flask', 'registrar logout')
      // A sessão local deve ser encerrada mesmo se a auditoria do logout falhar.
    }
  }

  clearAuthTokenCookie(event)
  clearActiveClinicaIdCookie(event)
  return { ok: true }
}
