import { listarPadroesDocumentos } from '../../features/clinico/service'

export default defineEventHandler(event => listarPadroesDocumentos(event))
