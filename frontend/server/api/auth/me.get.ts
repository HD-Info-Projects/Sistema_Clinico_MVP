export default defineEventHandler(async (event) => {
  try {
    const rawUser = await getAuthenticatedUser(event)
    return buildAuthSessionPayload(event, rawUser)
  } catch {
    throw createError({ statusCode: 401, statusMessage: 'Não autorizado' })
  }
})
