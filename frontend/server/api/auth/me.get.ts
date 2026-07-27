export default defineEventHandler(async (event) => {
  try {
    const rawUser = await getAuthenticatedUser(event)
    return buildAuthPayload(rawUser)
  } catch {
    throw createError({ statusCode: 401, statusMessage: 'Não autorizado' })
  }
})
