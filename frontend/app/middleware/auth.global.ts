import { useAuthStore, paginaInicialPorModo } from '~/stores/auth'

export default defineNuxtRouteMiddleware(async (to) => {
  const auth = useAuthStore()

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
    if (auth.isAdmin) return navigateTo(paginaInicialPorModo(auth.accessMode))
    if (['dpo', 'ti'].includes(auth.user?.role || '')) return navigateTo('/lgpd/auditoria')
    if (auth.isRecepcao) return navigateTo('/recepcao')
    return navigateTo('/dashboard')
  }

  if (to.path === '/acesso-negado') return

  // Seleção de modo de acesso — exclusiva de admins
  if (to.path === '/selecionar-acesso') {
    if (!auth.isAdmin) {
      if (['dpo', 'ti'].includes(auth.user?.role || '')) return navigateTo('/lgpd/auditoria')
      if (auth.isRecepcao) return navigateTo('/recepcao')
      return navigateTo('/dashboard')
    }
    return
  }

  // Seleção de unidade — admins podem acessar sempre; médico/recepção apenas com múltiplas clínicas
  if (to.path === '/selecionar-clinica') {
    if (auth.isAdmin) return
    if (auth.clinicas.length > 1 && (auth.isMedico || auth.isRecepcao)) return
    if (['dpo', 'ti'].includes(auth.user?.role || '')) return navigateTo('/lgpd/auditoria')
    if (auth.isRecepcao) return navigateTo('/recepcao')
    return navigateTo('/dashboard')
  }

  // Admin sem modo definido deve escolher o acesso antes de navegar
  if (auth.isAdmin && !auth.accessMode) {
    return navigateTo('/selecionar-acesso')
  }

  // Se tem múltiplas clínicas mas nenhuma selecionada, forçar seleção
  if (auth.clinicas.length > 1 && !auth.activeClinicaId) {
    if (!auth.isAdmin || auth.accessMode === 'recepcionista') {
      return navigateTo('/selecionar-clinica')
    }
  }

  // Role-based routing - proteger rotas por role
  const isAdminRoute = to.path.startsWith('/admin')
  const isLgpdRoute = to.path.startsWith('/lgpd')
  const canAccessLgpd = ['admin', 'dpo', 'ti'].includes(auth.user?.role || '')
  if (isLgpdRoute && !canAccessLgpd) {
    return navigateTo('/acesso-negado')
  }

  const isRecepcaoRoute = to.path.startsWith('/recepcao')
  const isDashboardRoute = to.path.startsWith('/dashboard')
    || to.path.startsWith('/agenda')
    || to.path.startsWith('/atendimento')
    || to.path.startsWith('/pacientes')
    || to.path.startsWith('/padroes')

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
    if (auth.isRecepcao) return navigateTo('/recepcao')
    if (canAccessLgpd) return navigateTo('/lgpd/auditoria')
    return navigateTo('/dashboard')
  }

  if (['dpo', 'ti'].includes(auth.user?.role || '') && !isLgpdRoute) {
    return navigateTo('/lgpd/auditoria')
  }

  // Recepção só pode acessar rotas /recepcao
  if (auth.isRecepcao && !isRecepcaoRoute && !isAdminRoute) {
    return navigateTo('/recepcao')
  }

  // Médico só pode acessar rotas médicas (dashboard, agenda, etc)
  if (auth.isMedico && !isDashboardRoute && !isAdminRoute && !isRecepcaoRoute) {
    return navigateTo('/dashboard')
  }
})
