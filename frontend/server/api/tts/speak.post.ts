import { readBody } from 'h3'
import { gerarAudioChamadoTts } from '../../features/chamadas/service'

export default defineEventHandler(async (event) => {
  const body = await readBody<{ chamadoId?: number, voice?: string }>(event)
  return gerarAudioChamadoTts(event, body)
})
