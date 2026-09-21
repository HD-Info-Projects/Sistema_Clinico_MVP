import { criarPadraoDocumento } from '../../features/clinico/service'

export default defineEventHandler(async (event) => {
  return criarPadraoDocumento(event, await readBody(event))
})
