export function useSalaAtendimento() {
  const auth = useAuthStore()
  const sala = useLocalStorage<string | null>('sala_atendimento', null)

  const legacyStorageKey = computed(() => {
    const usuarioId = auth.user?.id ?? 'anonimo'
    const clinicaId = auth.activeClinicaId ?? 'sem-unidade'
    return `sala_atendimento:${usuarioId}:${clinicaId}`
  })

  function extrairNumeroSala(valor: string | null) {
    const numero = valor?.match(/(?:consult[oó]rio\s*)?(\d+)/i)?.[1]
    return numero && Number(numero) > 0 ? numero : null
  }

  onMounted(() => {
    if (sala.value || !import.meta.client) return

    const valorAntigo = localStorage.getItem(legacyStorageKey.value)
    const numeroSala = extrairNumeroSala(valorAntigo)
    if (numeroSala) sala.value = numeroSala
  })

  function definirSala(novaSala: string) {
    const numeroSala = extrairNumeroSala(novaSala)
    if (numeroSala) sala.value = numeroSala
  }

  function limpar() {
    sala.value = null
  }

  return {
    sala: readonly(sala),
    precisaSelecionar: computed(() => !sala.value),
    definirSala,
    limpar
  }
}
