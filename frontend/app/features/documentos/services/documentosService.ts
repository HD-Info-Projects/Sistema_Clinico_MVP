import type { DocumentoMedico, DocumentoMedicoDados, DocumentoMedicoTipo } from '../types'

export function listarDocumentosPorAtendimento(medSpdataAtendimentoId: number | null) {
  return $fetch<DocumentoMedico[]>(`/api/documentos-medicos/${medSpdataAtendimentoId}`)
}

export function listarDocumentosPorIds(ids: number[]) {
  return $fetch<DocumentoMedico[]>('/api/documentos-medicos', {
    query: { ids: ids.join(',') }
  })
}

export function salvarDocumentoMedico(
  medSpdataAtendimentoId: number | null,
  tipo: DocumentoMedicoTipo,
  dados: DocumentoMedicoDados | Record<string, unknown>
) {
  return $fetch<DocumentoMedico>(`/api/documentos-medicos/${medSpdataAtendimentoId}/${tipo}`, {
    method: 'PUT',
    body: { dados }
  })
}
