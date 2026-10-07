import { registrarEventoAuditoria } from '~/utils/auditoria-eventos'

type ModuloAuditoria = {
  chave: string
  label: string
}

const MODULOS: { prefixo: string, modulo: ModuloAuditoria }[] = [
  { prefixo: '/admin', modulo: { chave: 'admin', label: 'Painel Admin' } },
  { prefixo: '/lgpd', modulo: { chave: 'lgpd', label: 'Auditoria LGPD' } },
  { prefixo: '/recepcao/noshow', modulo: { chave: 'no_show', label: 'No-show' } },
  { prefixo: '/recepcao/retencao-exames', modulo: { chave: 'conversao_exames', label: 'Conversao de exames' } },
  { prefixo: '/recepcao/novo-atendimento', modulo: { chave: 'cadastro_atendimento', label: 'Cadastro de Atendimento' } },
  { prefixo: '/recepcao/agenda', modulo: { chave: 'agenda_recepcao', label: 'Agenda da Recep' } },
  { prefixo: '/recepcao', modulo: { chave: 'dashboard_recepcao', label: 'Dashboard da Recep' } },
  { prefixo: '/atendimento', modulo: { chave: 'atendimento_medico', label: 'Atendimento medico' } },
  { prefixo: '/pacientes', modulo: { chave: 'pacientes', label: 'Pacientes' } },
  { prefixo: '/agenda', modulo: { chave: 'agenda_medica', label: 'Agenda medica' } },
  { prefixo: '/padroes', modulo: { chave: 'padroes_medicos', label: 'Padroes medicos' } },
  { prefixo: '/dashboard', modulo: { chave: 'dashboard', label: 'Dashboard' } }
]

function moduloPorRota(path: string): ModuloAuditoria | null {
  return MODULOS.find(item => path.startsWith(item.prefixo))?.modulo ?? null
}

export default defineNuxtPlugin(() => {
  const router = useRouter()
  const auth = useAuthStore()

  router.afterEach((to, from) => {
    if (!auth.user) return

    const origem = moduloPorRota(from.path)
    const destino = moduloPorRota(to.path)
    if (origem?.chave === destino?.chave) return

    if (origem) {
      registrarEventoAuditoria({
        acao: 'SAIU_MODULO',
        entidade: 'modulo',
        descricao: `Saida do modulo ${origem.label}. rota=${from.path}`
      })
    }

    if (destino) {
      registrarEventoAuditoria({
        acao: 'ENTROU_MODULO',
        entidade: 'modulo',
        descricao: `Entrada no modulo ${destino.label}. rota=${to.path}`
      })
    }
  })
})
