import type { DocumentoMedico, DocumentoMedicoDados, DocumentoMedicoTipo } from '../types'
import type { DocumentoPersonalizado } from '~/types'

export function listarDocumentosPorAtendimento(medSpdataAtendimentoId: number | null) {
  return $fetch<(DocumentoMedico | DocumentoPersonalizado)[]>(`/api/documentos-medicos/${medSpdataAtendimentoId}`)
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

export function salvarDocumentoPersonalizado(
  medSpdataAtendimentoId: number | null,
  dados: { titulo: string, conteudo: string },
  documentoId?: number
) {
  const url = documentoId
    ? `/api/documentos-medicos/${medSpdataAtendimentoId}/personalizados/${documentoId}`
    : `/api/documentos-medicos/${medSpdataAtendimentoId}/personalizados`

  return $fetch<DocumentoPersonalizado>(url, {
    method: documentoId ? 'PUT' : 'POST',
    body: { dados }
  })
}

export function excluirDocumentoPersonalizado(
  medSpdataAtendimentoId: number | null,
  documentoId: number
) {
  return $fetch<{ ok: boolean }>(
    `/api/documentos-medicos/${medSpdataAtendimentoId}/personalizados/${documentoId}`,
    { method: 'DELETE' }
  )
}
