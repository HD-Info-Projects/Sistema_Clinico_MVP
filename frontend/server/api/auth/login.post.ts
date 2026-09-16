import { loginAuth } from '../../features/auth/service'

export default defineEventHandler(async (event) => {
  const body = await readBody(event)
  return await loginAuth(event, body)
})
