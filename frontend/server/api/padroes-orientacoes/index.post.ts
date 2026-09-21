import { criarPadraoOrientacao } from '../../features/clinico/service'

export default defineEventHandler(async (event) => {
  const body = await readBody(event)
  return await criarPadraoOrientacao(event, body)
})
