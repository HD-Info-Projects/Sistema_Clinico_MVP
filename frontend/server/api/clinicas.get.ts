export default defineEventHandler(async (event) => {
  const rawUser = await getAuthenticatedUser(event)
  return clinicasFromBackend(rawUser)
})
