import type { H3Event } from 'h3'
import { fetchErrorStatus } from '../../utils/proxy-error'
import { setPrivateNoStore } from '../../utils/response'

export async function loginAuth(event: H3Event, body: { email?: string, password?: string }) {
  setPrivateNoStore(event)
  const { email, password } = body
  const config = useRuntimeConfig()

  let res: { access_token?: string }
  try {
    res = await $fetch(`${config.flaskBaseUrl}/login/auth`, {
      method: 'POST',
      body: { email, senha: password }
    })
  } catch (error: unknown) {
    const status = fetchErrorStatus(error)

    if (status === 400 || status === 401 || status === 429) {
      throw createError({
        statusCode: status,
        statusMessage: status === 429 ? 'Muitas tentativas de login' : 'Credenciais inválidas'
      })
    }

    console.error('[auth] Falha ao autenticar no Flask', { status })
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
        Authorization: `Bearer ${res.access_token}`
      }
    })

    setAuthTokenCookie(event, res.access_token)
    return buildLoginSessionPayload(event, rawUser as Parameters<typeof buildLoginSessionPayload>[1])
  } catch (error: unknown) {
    const status = fetchErrorStatus(error)
    console.error('[auth] Falha ao validar sessão recém-criada', { status })
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
  const token = getCookie(event, AUTH_COOKIE_NAME)
  if (token) {
    const config = useRuntimeConfig()
    try {
      await $fetch(`${config.flaskBaseUrl}/login/logout`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${token}`
        }
      })
    } catch {
      // A sessão local deve ser encerrada mesmo se a auditoria do logout falhar.
    }
  }

  clearAuthTokenCookie(event)
  clearActiveClinicaIdCookie(event)
  return { ok: true }
}
