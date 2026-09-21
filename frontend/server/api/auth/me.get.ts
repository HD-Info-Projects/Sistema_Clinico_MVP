import { buscarSessaoAuth } from '../../features/auth/service'

export default defineEventHandler(async (event) => {
  return await buscarSessaoAuth(event)
})
