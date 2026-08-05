import { useAuthStore } from '~/stores/auth'

export default defineNuxtRouteMiddleware(async (to) => {
  const auth = useAuthStore()

  // Páginas públicas que não precisam de autenticação
  if (to.path === '/painel-chamada') return
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
    if (auth.isRecepcao) return navigateTo('/recepcao')
    return navigateTo('/dashboard')
  }

  // Rota de seleção de clínica — permitir se não tiver clínica ativa
  if (to.path === '/selecionar-clinica') {
    if (auth.activeClinicaId) {
      if (auth.isAdmin) return navigateTo('/admin')
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
  const isRecepcaoRoute = to.path.startsWith('/recepcao')
  const isDashboardRoute = to.path.startsWith('/dashboard')
    || to.path.startsWith('/agenda')
    || to.path.startsWith('/atendimento')
    || to.path.startsWith('/pacientes')
    || to.path.startsWith('/padroes')

  // Admin só pode acessar rotas /admin
  if (auth.isAdmin && !isAdminRoute) {
    return navigateTo('/admin')
  }

  // Não-admin não pode acessar rotas /admin
  if (!auth.isAdmin && isAdminRoute) {
    if (auth.isRecepcao) return navigateTo('/recepcao')
    return navigateTo('/dashboard')
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
