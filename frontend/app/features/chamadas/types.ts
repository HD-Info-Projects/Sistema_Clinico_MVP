import type { Chamado } from '~/types'

export type { Chamado }
export type ChamadoStatus = Chamado['status']
export type CriarChamadoPayload = Pick<Chamado, 'pacienteId' | 'pacienteNome' | 'localAtendimento' | 'medicoResponsavel'>

export type GerarAudioChamadoOptions = {
  voice?: string
  signal?: AbortSignal
}
