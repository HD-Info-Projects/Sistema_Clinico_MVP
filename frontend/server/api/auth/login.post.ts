function fetchStatus(error: unknown) {
  const fetchError = error as { status?: number, statusCode?: number, response?: { status?: number } }
  return fetchError.response?.status || fetchError.statusCode || fetchError.status
}

export default defineEventHandler(async (event) => {
  const body = await readBody(event)
  const { email, password } = body
  const config = useRuntimeConfig()

  let res: { access_token?: string }
  try {
    res = await $fetch(`${config.flaskBaseUrl}/login/auth`, {
      method: 'POST',
      body: { email, senha: password }
    })
  } catch (error: unknown) {
    const status = fetchStatus(error)

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

  setAuthTokenCookie(event, res.access_token)

  try {
    const rawUser = await $fetch(`${config.flaskBaseUrl}/login/me`, {
      headers: {
        Authorization: `Bearer ${res.access_token}`
      }
    })

    return buildLoginSessionPayload(event, rawUser as Parameters<typeof buildLoginSessionPayload>[1])
  } catch (error: unknown) {
    clearAuthTokenCookie(event)
    console.error('[auth] Falha ao validar sessão recém-criada', { status: fetchStatus(error) })
    throw createError({ statusCode: 502, statusMessage: 'Falha ao carregar sessão' })
  }
})
