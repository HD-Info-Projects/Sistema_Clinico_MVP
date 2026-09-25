import { useAuthStore, paginaInicialPorModo } from '~/stores/auth'
import { COORD_RECEPCAO_ROLES, LGPD_ROLES, MEDICO_ROLES, RECEPCAO_ROLES, roleIn } from '~/utils/roles'

export default defineNuxtRouteMiddleware(async (to) => {
  const auth = useAuthStore()

  function destinoPrincipal() {
    const role = auth.user?.role
    if (auth.isAdmin) return paginaInicialPorModo(auth.accessMode)
    if (roleIn(role, LGPD_ROLES)) return '/lgpd/auditoria'
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
    if (auth.clinicas.length > 1 && (auth.isMedico || auth.isRecepcao)) return
    return navigateTo(destinoPrincipal())
  }

  // Admin sem modo definido deve escolher o acesso antes de navegar
  if (auth.isAdmin && !auth.accessMode) {
    return navigateTo('/selecionar-acesso')
  }

  // Se tem múltiplas clínicas mas nenhuma selecionada, forçar seleção
  if (auth.clinicas.length > 1 && !auth.activeClinicaId) {
    if ((auth.isMedico || auth.isRecepcao) && (!auth.isAdmin || auth.accessMode === 'recepcionista')) {
      return navigateTo('/selecionar-clinica')
    }
  }

  // Role-based routing - proteger rotas por role
  const isAdminRoute = to.path.startsWith('/admin')
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
  const isDashboardRoute = to.path.startsWith('/dashboard')
    || to.path.startsWith('/agenda')
    || to.path.startsWith('/atendimento')
    || to.path.startsWith('/pacientes')
    || to.path.startsWith('/padroes')
  const canAccessMedico = roleIn(auth.user?.role, MEDICO_ROLES)

  // Guardas por modo de acesso do admin
  if (auth.isAdmin) {
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
    if (!isAdminRoute && !isLgpdRoute) return navigateTo('/admin')
    return
  }

  // Não-admin não pode acessar rotas /admin
  if (isAdminRoute) {
    return navigateTo(destinoPrincipal())
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

  if (isDashboardRoute && !canAccessMedico) {
    return navigateTo(destinoPrincipal())
  }

  // Médico só pode acessar rotas médicas (dashboard, agenda, etc)
  if (canAccessMedico && !isDashboardRoute && !isAdminRoute && !isRecepcaoRoute) {
    return navigateTo('/dashboard')
  }

  if (!canAccessLgpd && !canAccessRecepcao && !canAccessMedico) {
    return navigateTo('/acesso-negado')
  }
})
