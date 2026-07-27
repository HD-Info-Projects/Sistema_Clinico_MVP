export default defineEventHandler((event) => {
  clearAuthTokenCookie(event)
  return { ok: true }
})
