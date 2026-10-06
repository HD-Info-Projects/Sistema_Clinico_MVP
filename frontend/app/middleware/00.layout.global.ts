export default defineNuxtRouteMiddleware((to) => {
  // Set layout before rendering, including SSR and hydration redirects.
  // Explicit page metadata (including layout: false) takes precedence.
  if (to.meta.layout !== undefined) return

  const path = to.path
  if (path === '/acesso-negado') to.meta.layout = false
  else if (['/login', '/selecionar-clinica', '/selecionar-acesso'].includes(path)) to.meta.layout = 'auth'
  else if (path.startsWith('/painel-chamada')) to.meta.layout = 'tv'
  else if (path === '/atendimento-medico') to.meta.layout = 'atendimento'
  else if (path.startsWith('/recepcao')) to.meta.layout = 'recepcao'
  else if (path.startsWith('/admin')) to.meta.layout = 'admin'
  else to.meta.layout = 'default'
})
