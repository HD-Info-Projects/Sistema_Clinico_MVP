export type AuditoriaEventoAcao
  = | 'ENTROU_MODULO'
    | 'SAIU_MODULO'
    | 'TROCOU_ACESSO'
    | 'MUDOU_UNIDADE'
    | 'ABRIU_PACIENTE'
    | 'CANCELOU_ACAO'

export type AuditoriaEventoPayload = {
  acao: AuditoriaEventoAcao
  entidade: string
  entidade_id?: number
  descricao?: string
}

export function registrarEventoAuditoria(payload: AuditoriaEventoPayload) {
  if (!import.meta.client) return

  void $fetch('/api/auditorias', {
    method: 'POST',
    body: payload
  }).catch(() => {
    // Auditoria complementar nao deve bloquear a operacao do usuario.
  })
}
