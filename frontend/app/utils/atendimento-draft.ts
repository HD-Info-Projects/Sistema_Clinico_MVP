import type { ConsultaStatusPayload } from '~/features/agenda/services/agendaService'

// Rascunho do atendimento médico (sessionStorage). A página de atendimento é a
// dona do formato completo; aqui ficam só a chave e a leitura do conteúdo
// clínico para finalizar um atendimento pendente fora daquela tela.
export const ATENDIMENTO_DRAFT_PREFIX = 'medsystem:atendimento-draft:'
export const ATENDIMENTO_DRAFT_TTL_MS = 7 * 24 * 60 * 60 * 1000

export function chaveDraftAtendimento(agendamentoId: number, pacienteId: number | null | undefined) {
  return `${ATENDIMENTO_DRAFT_PREFIX}${agendamentoId}:${pacienteId}`
}

type DraftClinico = {
  savedAt?: string
  anamneseTexto?: string
  cidSelecionadoLista?: { cid: string, nome?: string }[]
  receitaTexto?: string
  examesSelecionados?: {
    nome: string
    exameId?: number | null
    codigo_amb?: string | null
    codigo_alfanumerico?: string | null
    orientacao?: string | null
  }[]
}

/** Converte o rascunho salvo no navegador no payload de finalização, se houver conteúdo. */
export function lerConsultaDoDraft(agendamentoId: number, pacienteId: number | null | undefined): ConsultaStatusPayload | null {
  if (!import.meta.client) return null

  const raw = sessionStorage.getItem(chaveDraftAtendimento(agendamentoId, pacienteId))
  if (!raw) return null

  try {
    const draft = JSON.parse(raw) as DraftClinico
    const savedAt = draft.savedAt ? new Date(draft.savedAt).getTime() : 0
    if (!savedAt || Date.now() - savedAt > ATENDIMENTO_DRAFT_TTL_MS) return null

    const consulta: ConsultaStatusPayload = {
      anamnese: draft.anamneseTexto || '',
      diagnosticos: (draft.cidSelecionadoLista ?? []).map((cid, i) => ({
        cid: cid.cid,
        descricao: cid.nome,
        principal: i === 0
      })),
      medicamentos: draft.receitaTexto || '',
      exames: (draft.examesSelecionados ?? []).map(e => ({
        nome: e.nome,
        exame_id: e.exameId ?? null,
        codigo_amb: e.codigo_amb ?? null,
        codigo_alfanumerico: e.codigo_alfanumerico ?? null,
        orientacao: e.orientacao ?? null
      }))
    }

    const temConteudo = Boolean(
      consulta.anamnese?.trim()
      || consulta.diagnosticos?.length
      || consulta.medicamentos?.trim()
      || consulta.exames?.length
    )
    return temConteudo ? consulta : null
  } catch {
    return null
  }
}

export function removerDraftAtendimento(agendamentoId: number, pacienteId: number | null | undefined) {
  if (!import.meta.client) return
  const chave = chaveDraftAtendimento(agendamentoId, pacienteId)
  sessionStorage.removeItem(chave)
  localStorage.removeItem(chave)
}
