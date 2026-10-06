export default defineNuxtRouteMiddleware(async () => {
  if (import.meta.server) return

  const auth = useAuthStore()
  const agendamentosStore = useAgendamentosStore()
  const toast = useToast()
  const usuarioId = auth.user?.id
  const clinicaId = auth.activeClinicaId

  if (!usuarioId || !clinicaId) {
    return navigateTo('/dashboard', { replace: true })
  }

  const chave = `${usuarioId}:${clinicaId}`
  const resultado = await agendamentosStore.garantirAtendimentoAtual({
    chave,
    clinicaId,
    medicoId: usuarioId
  })

  if (resultado.status === 'absent') {
    return navigateTo('/dashboard', { replace: true })
  }
  if (resultado.status === 'cancelled') {
    return navigateTo('/dashboard', { replace: true })
  }
  if (resultado.status !== 'present') {
    toast.add({
      title: 'Não foi possível verificar o atendimento',
      description: 'Tente acessar novamente pelo menu Atendimento Médico.',
      color: 'error',
      icon: 'i-lucide-wifi-off'
    })
    return navigateTo('/dashboard', { replace: true })
  }
})
