import type { ProcedimentoCatalogo } from '../types'

export type BuscarProcedimentosResponse = {
  procedimentos: ProcedimentoCatalogo[]
}

export function buscarProcedimentosCatalogo(q: string, signal?: AbortSignal) {
  return $fetch<BuscarProcedimentosResponse>('/api/procedimentos/buscar', {
    query: { q },
    signal
  })
}
