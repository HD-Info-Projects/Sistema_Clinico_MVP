import { z } from 'zod'
import { loginAuth } from '../../features/auth/service'

const loginSchema = z.object({
  username: z.string().trim().min(1).max(254),
  password: z.string().min(1).max(256)
})

export default defineEventHandler(async (event) => {
  const body = await readBodyWithSchema(event, loginSchema, 'Usuário e senha inválidos')
  return await loginAuth(event, body)
})
