import { logoutAuth } from '../../features/auth/service'

export default defineEventHandler(async (event) => {
  return await logoutAuth(event)
})
