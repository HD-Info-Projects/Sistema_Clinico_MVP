/**
 * Estado compartilhado entre o layout de atendimento e a página de atendimento médico
 * para controlar a saída da tela enquanto há um atendimento em andamento.
 *
 * - `saidaLiberada`: quando true, o guard de navegação da página deixa a rota ser trocada
 *   (usado após pausar, finalizar, cancelar ou redirecionamentos automáticos).
 * - `destinoPendente`: rota que o médico tentou acessar quando o modal foi aberto.
 */
export function useSaidaAtendimento() {
  const saidaLiberada = useState<boolean>('atendimento:saida-liberada', () => false)
  const destinoPendente = useState<string | null>('atendimento:destino-pendente', () => null)
  const encerramentoEmAndamento = useState<'finalizar' | 'cancelar' | null>(
    'atendimento:encerramento-em-andamento',
    () => null
  )

  function liberarSaida() {
    saidaLiberada.value = true
  }

  function bloquearSaida() {
    saidaLiberada.value = false
  }

  function resetarSaida() {
    saidaLiberada.value = false
    destinoPendente.value = null
    encerramentoEmAndamento.value = null
  }

  return {
    saidaLiberada,
    destinoPendente,
    encerramentoEmAndamento,
    liberarSaida,
    bloquearSaida,
    resetarSaida
  }
}
