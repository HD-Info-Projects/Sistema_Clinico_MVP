import { defineStore } from 'pinia'
import type { AuthUser, Clinica } from '~/types'

type AuthSessionResponse = {
  user: AuthUser
  clinicas: Clinica[]
  activeClinicaId?: number | null
}

export const useAuthStore = defineStore('auth', () => {
  const user = ref<AuthUser | null>(null)
  const clinicas = ref<Clinica[]>([])
  const sessionChecked = ref(false)

  const isLoggedIn = computed(() => !!user.value)

  function normalizarClinicaId(value: unknown) {
    const id = Number(value)
    return Number.isInteger(id) && id > 0 ? id : null
  }

  const activeClinicaId = ref<number | null>(null)

  function selecionarClinicaAtiva(id: number | null) {
    activeClinicaId.value = normalizarClinicaId(id)
  }

  function clinicaExisteNaLista(id: number | null, lista = clinicas.value) {
    return !!id && lista.some(c => c.id === id)
  }

  function aplicarSessao(response: AuthSessionResponse) {
    user.value = response.user
    clinicas.value = response.clinicas

    const clinicaId = normalizarClinicaId(response.activeClinicaId)
    if (clinicaExisteNaLista(clinicaId, response.clinicas)) {
      selecionarClinicaAtiva(clinicaId)
    } else if (response.clinicas.length === 1) {
      selecionarClinicaAtiva(response.clinicas[0]!.id)
    } else {
      selecionarClinicaAtiva(null)
    }

    sessionChecked.value = true
  }

  const activeClinica = computed(() => {
    if (!activeClinicaId.value) return null
    return clinicas.value.find(c => c.id === activeClinicaId.value) ?? null
  })

  watch(clinicas, (lista) => {
    if (activeClinicaId.value && !lista.some(c => c.id === activeClinicaId.value)) {
      selecionarClinicaAtiva(null)
    }
  })

  const isMedico = computed(() => user.value?.role === 'medico')
  const isRecepcao = computed(() => user.value?.role === 'recepcao')

  function limparRascunhosClinicosLocais() {
    if (!import.meta.client) return

    for (const storage of [sessionStorage, localStorage]) {
      for (const key of Object.keys(storage)) {
        if (key.startsWith('medsystem:atendimento-draft:')) {
          storage.removeItem(key)
        }
      }
    }
  }

  async function login(credentials: Record<string, unknown>) {
    try {
      const response = await $fetch<AuthSessionResponse>('/api/auth/login', {
        method: 'POST',
        body: credentials
      })

      aplicarSessao(response)

      if (response.clinicas.length > 1 && !activeClinicaId.value) {
        navigateTo('/selecionar-clinica')
      } else {
        if (['admin', 'dpo', 'ti'].includes(response.user.role)) {
          navigateTo('/lgpd/auditoria')
        } else if (response.user.role === 'recepcao') {
          navigateTo('/recepcao')
        } else {
          navigateTo('/')
        }
      }

      return { success: true }
    } catch (error: unknown) {
      const fetchError = error as { data?: { statusMessage?: string } }
      return {
        success: false,
        message: fetchError.data?.statusMessage || 'Erro ao realizar login'
      }
    }
  }

  async function logout() {
    if (import.meta.client) useSse().disconnect()
    limparRascunhosClinicosLocais()

    try {
      await $fetch('/api/auth/logout', { method: 'POST' })
    } catch {
      // A limpeza local ainda deve ocorrer se o servidor já encerrou a sessão.
    }

    user.value = null
    clinicas.value = []
    selecionarClinicaAtiva(null)
    sessionChecked.value = true
    navigateTo('/login')
  }

  async function fetchUser() {
    if (user.value) return true

    try {
      const response = await $fetch<AuthSessionResponse>('/api/auth/me')
      aplicarSessao(response)
      return true
    } catch {
      user.value = null
      clinicas.value = []
      selecionarClinicaAtiva(null)
      sessionChecked.value = true
      return false
    }
  }

  async function setActiveClinica(id: number) {
    const clinicaId = normalizarClinicaId(id)
    if (!clinicaId || !clinicaExisteNaLista(clinicaId)) return false

    try {
      const response = await $fetch<{ activeClinicaId: number }>('/api/clinicas/ativa', {
        method: 'POST',
        body: { unidadeId: clinicaId }
      })
      const activeId = normalizarClinicaId(response.activeClinicaId)
      if (!activeId || !clinicaExisteNaLista(activeId)) return false

      selecionarClinicaAtiva(activeId)
      return true
    } catch {
      return false
    }
  }

  return {
    user,
    clinicas,
    sessionChecked,
    activeClinicaId,
    activeClinica,
    isLoggedIn,
    isMedico,
    isRecepcao,
    login,
    logout,
    fetchUser,
    setActiveClinica
  }
})
