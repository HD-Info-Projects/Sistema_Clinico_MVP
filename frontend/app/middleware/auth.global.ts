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

  // Rota de seleção de clínica — permitir se não tiver clínica ativa
  if (to.path === '/selecionar-clinica') {
    if (auth.activeClinicaId) {
      return navigateTo(auth.isRecepcao ? '/recepcao' : '/dashboard')
    }
    return
  }

  // Se tem múltiplas clínicas mas nenhuma selecionada, forçar seleção
  if (auth.clinicas.length > 1 && !auth.activeClinicaId) {
    return navigateTo('/selecionar-clinica')
  }

  // Role-based routing
  const isRecepcaoRoute = to.path.startsWith('/recepcao')
  const isMedicoRoute = !isRecepcaoRoute

  if (auth.user?.role === 'recepcao' && isMedicoRoute) {
    return navigateTo('/recepcao')
  }

  if (auth.user?.role === 'medico' && isRecepcaoRoute) {
    return navigateTo('/dashboard')
  }
})
