import type { ExamesPacsResponse } from '~/types'

export function buscarExamesPacs(pacienteId: number) {
  return $fetch<ExamesPacsResponse>(`/api/exames-pacs/paciente/${pacienteId}`)
}

export function abrirExamePacs(idTokenLancamentoExame: number | null | undefined, tipo: 'imagem' | 'laudo') {
  if (!import.meta.client || !idTokenLancamentoExame) return
  const id = Number(idTokenLancamentoExame)
  if (!Number.isFinite(id) || id <= 0) return

  const url = tipo === 'imagem'
    ? `/api/exames-pacs/${id}/viewer`
    : `/api/exames-pacs/${id}/laudo/pdf`
  window.open(url, '_blank', 'noopener,noreferrer')
}
