import { useAuthStore, paginaInicialPorModo } from '~/stores/auth'
import { ASSISTENTE_ROLES, COORD_RECEPCAO_ROLES, FINANCEIRO_ROLES, LGPD_ROLES, MEDICO_ROLES, RECEPCAO_ROLES, roleIn } from '~/utils/roles'

export default defineNuxtRouteMiddleware(async (to) => {
  const auth = useAuthStore()

  function destinoPrincipal() {
    const role = auth.user?.role
    if (auth.isAdmin) return paginaInicialPorModo(auth.accessMode)
    if (roleIn(role, LGPD_ROLES)) return '/lgpd/auditoria'
    if (roleIn(role, FINANCEIRO_ROLES)) return '/financeiro/pagamentos'
    if (roleIn(role, ASSISTENTE_ROLES)) return '/dashboard'
    if (roleIn(role, RECEPCAO_ROLES)) return '/recepcao'
    if (roleIn(role, MEDICO_ROLES)) return '/dashboard'
    return '/acesso-negado'
  }

  // Páginas públicas que não precisam de autenticação
  if (to.path.startsWith('/painel-chamada')) return
  if (to.path === '/login') return

  if (import.meta.server) return

  // Garantir que os dados do usuário estejam carregados
  if (!auth.user) {
    const authenticated = await auth.fetchUser()
    if (!authenticated) return navigateTo('/login')
  }

  // Redirecionar para login se não estiver logado
  if (!auth.isLoggedIn) {
    return navigateTo('/login')
  }

  // Rota raiz - redirecionar baseado no role
  if (to.path === '/') {
    return navigateTo(destinoPrincipal())
  }

  if (to.path === '/acesso-negado') return

  // Seleção de modo de acesso — exclusiva de admins
  if (to.path === '/selecionar-acesso') {
    if (!auth.isAdmin) {
      return navigateTo(destinoPrincipal())
    }
    return
  }

  // Seleção de unidade — admins podem acessar sempre; médico/recepção apenas com múltiplas clínicas
  if (to.path === '/selecionar-clinica') {
    if (auth.isAdmin) return
    if (auth.clinicas.length > 1 && (auth.isMedico || auth.isAssistente || auth.isRecepcao || auth.canAccessFinanceiro)) return
    return navigateTo(destinoPrincipal())
  }

  // Admin sem modo definido deve escolher o acesso antes de navegar
  if (auth.isAdmin && !auth.accessMode) {
    return navigateTo('/selecionar-acesso')
  }

  // Se tem múltiplas clínicas mas nenhuma selecionada, forçar seleção
  if (auth.clinicas.length > 1 && !auth.activeClinicaId) {
    if ((auth.isMedico || auth.isAssistente || auth.isRecepcao) && (!auth.isAdmin || auth.accessMode === 'recepcionista')) {
      return navigateTo('/selecionar-clinica')
    }
  }

  // Role-based routing - proteger rotas por role
  const isAdminRoute = to.path.startsWith('/admin')
  const isFinanceiroRoute = to.path === '/financeiro' || to.path.startsWith('/financeiro/')
  const canAccessFinanceiro = roleIn(auth.user?.role, FINANCEIRO_ROLES)
  if (isFinanceiroRoute && !canAccessFinanceiro) {
    return navigateTo('/acesso-negado')
  }
  const isLgpdRoute = to.path.startsWith('/lgpd')
  const canAccessLgpd = roleIn(auth.user?.role, LGPD_ROLES)
  if (isLgpdRoute && !canAccessLgpd) {
    return navigateTo('/acesso-negado')
  }

  const isRecepcaoRoute = to.path.startsWith('/recepcao')
  const isCoordRecepcaoRoute = to.path.startsWith('/recepcao/noshow')
    || to.path.startsWith('/recepcao/retencao-exames')
  const canAccessRecepcao = roleIn(auth.user?.role, RECEPCAO_ROLES)
  const canAccessCoordRecepcao = roleIn(auth.user?.role, COORD_RECEPCAO_ROLES)
  const isDashboardRoute = to.path === '/dashboard'
  const isAssistenteRoute = to.path === '/dashboard'
  const isMedicoRoute = isDashboardRoute
    || to.path.startsWith('/agenda')
    || to.path.startsWith('/atendimento')
    || to.path.startsWith('/pacientes')
    || to.path.startsWith('/padroes')
  const canAccessMedico = roleIn(auth.user?.role, MEDICO_ROLES)
  const canAccessAssistente = roleIn(auth.user?.role, ASSISTENTE_ROLES)

  // Guardas por modo de acesso do admin
  if (auth.isAdmin) {
    if (auth.accessMode === 'financeiro') {
      if (!isFinanceiroRoute) return navigateTo('/financeiro/pagamentos')
      return
    }
    if (auth.accessMode === 'recepcionista') {
      if (!isRecepcaoRoute) return navigateTo('/recepcao')
      if (!auth.activeClinicaId) return navigateTo('/selecionar-clinica')
      return
    }
    if (auth.accessMode === 'logs') {
      if (!isLgpdRoute) return navigateTo('/lgpd/auditoria')
      return
    }
    // Modo administrador: painel admin + telas LGPD liberadas para admin.
    if (!isAdminRoute && !isLgpdRoute && !isFinanceiroRoute) return navigateTo('/admin')
    return
  }

  // Não-admin não pode acessar rotas /admin
  if (isAdminRoute) {
    return navigateTo(destinoPrincipal())
  }

  if (canAccessFinanceiro) {
    if (!isFinanceiroRoute) return navigateTo('/financeiro/pagamentos')
    return
  }

  if (canAccessLgpd && !isLgpdRoute) {
    return navigateTo('/lgpd/auditoria')
  }

  if (isRecepcaoRoute && !canAccessRecepcao) {
    return navigateTo('/acesso-negado')
  }

  if (isCoordRecepcaoRoute && !canAccessCoordRecepcao) {
    return navigateTo('/recepcao')
  }

  // Recepção só pode acessar rotas /recepcao
  if (canAccessRecepcao && !isRecepcaoRoute && !isAdminRoute) {
    return navigateTo('/recepcao')
  }

  if (isMedicoRoute && !canAccessMedico && !(isAssistenteRoute && canAccessAssistente)) {
    return navigateTo(destinoPrincipal())
  }

  // Assistente médico só pode acessar o dashboard operacional.
  if (canAccessAssistente && !isAssistenteRoute && !isAdminRoute) {
    return navigateTo('/dashboard')
  }

  // Médico só pode acessar rotas médicas (dashboard, agenda, etc)
  if (canAccessMedico && !isMedicoRoute && !isAdminRoute && !isRecepcaoRoute) {
    return navigateTo('/dashboard')
  }

  if (!canAccessLgpd && !canAccessRecepcao && !canAccessMedico && !canAccessAssistente) {
    return navigateTo('/acesso-negado')
  }
})
