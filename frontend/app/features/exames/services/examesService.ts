import type { ExameCatalogo } from '../types'

export type BuscarExamesResponse = {
  exames: ExameCatalogo[]
}

export function buscarExamesCatalogo(q: string, signal?: AbortSignal) {
  return $fetch<BuscarExamesResponse>('/api/exames/buscar', {
    query: { q },
    signal
  })
}
