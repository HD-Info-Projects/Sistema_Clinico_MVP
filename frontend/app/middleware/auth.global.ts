import { useAuthStore } from '~/stores/auth'

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
    if (auth.isAdmin) return navigateTo('/admin')
    if (['dpo', 'ti'].includes(auth.user?.role || '')) return navigateTo('/lgpd/auditoria')
    if (auth.isRecepcao) return navigateTo('/recepcao')
    return navigateTo('/dashboard')
  }

  if (to.path === '/acesso-negado') return

  // Rota de seleção de clínica — permitir se não tiver clínica ativa
  if (to.path === '/selecionar-clinica') {
    if (auth.activeClinicaId) {
      if (auth.isAdmin) return navigateTo('/admin')
      if (['dpo', 'ti'].includes(auth.user?.role || '')) return navigateTo('/lgpd/auditoria')
      if (auth.isRecepcao) return navigateTo('/recepcao')
      return navigateTo('/dashboard')
    }
    return
  }

  // Se tem múltiplas clínicas mas nenhuma selecionada, forçar seleção
  if (auth.clinicas.length > 1 && !auth.activeClinicaId) {
    return navigateTo('/selecionar-clinica')
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

  // Admin acessa o painel administrativo e as telas LGPD liberadas para admin.
  if (auth.isAdmin && !isAdminRoute && !isLgpdRoute) {
    return navigateTo('/admin')
  }

  // Não-admin não pode acessar rotas /admin
  if (!auth.isAdmin && isAdminRoute) {
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
