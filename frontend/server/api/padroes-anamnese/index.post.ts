import { criarPadraoAnamnese } from '../../features/clinico/service'

export default defineEventHandler(async (event) => {
  const body = await readBody(event)
  return await criarPadraoAnamnese(event, body)
})
