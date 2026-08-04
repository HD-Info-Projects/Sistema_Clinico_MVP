export function useSalaAtendimento() {
  const auth = useAuthStore()
  const stored = ref<string | null>(null)

  const storageKey = computed(() => {
    const usuarioId = auth.user?.id ?? 'anonimo'
    const clinicaId = auth.activeClinicaId ?? 'sem-unidade'
    return `sala_atendimento:${usuarioId}:${clinicaId}`
  })

  function carregar() {
    if (!import.meta.client) return
    stored.value = localStorage.getItem(storageKey.value)
  }

  watch(storageKey, carregar, { immediate: true })

  const sala = readonly(computed(() => stored.value))
  const precisaSelecionar = computed(() => !stored.value)

  function definirSala(novaSala: string) {
    stored.value = novaSala
    if (import.meta.client) localStorage.setItem(storageKey.value, novaSala)
  }

  function limpar() {
    stored.value = null
    if (import.meta.client) localStorage.removeItem(storageKey.value)
  }

  return { sala, precisaSelecionar, definirSala, limpar }
}
