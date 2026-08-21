export default defineEventHandler(async (event) => {
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
})
