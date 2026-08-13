import { defineStore } from 'pinia'
import type { AuthUser, Clinica } from '~/types'

export const useAuthStore = defineStore('auth', () => {
  const config = useRuntimeConfig()
  const authCookieMaxAgeSeconds = Number(config.public.authCookieMaxAgeSeconds) || 60 * 60 * 24 * 7
  const user = ref<AuthUser | null>(null)
  const clinicas = ref<Clinica[]>([])
  const sessionChecked = ref(false)

  const isLoggedIn = computed(() => !!user.value)

  const _activeClinicaCookie = useCookie('active_clinica_id', {
    maxAge: authCookieMaxAgeSeconds
  })

  function normalizarClinicaId(value: unknown) {
    const id = Number(value)
    return Number.isInteger(id) && id > 0 ? id : null
  }

  const activeClinicaId = ref<number | null>(
    normalizarClinicaId(_activeClinicaCookie.value)
  )
  if (_activeClinicaCookie.value && activeClinicaId.value === null) {
    _activeClinicaCookie.value = null
  }

  watch(activeClinicaId, (val) => {
    const id = normalizarClinicaId(val)
    _activeClinicaCookie.value = id !== null ? String(id) : null
  })

  const activeClinica = computed(() => {
    if (!activeClinicaId.value) return null
    return clinicas.value.find(c => c.id === activeClinicaId.value) ?? null
  })

  watch(clinicas, (lista) => {
    if (activeClinicaId.value && !lista.some(c => c.id === activeClinicaId.value)) {
      activeClinicaId.value = null
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
      const response = await $fetch<{ user: AuthUser, clinicas: Clinica[] }>('/api/auth/login', {
        method: 'POST',
        body: credentials
      })

      user.value = response.user
      clinicas.value = response.clinicas
      sessionChecked.value = true

      if (response.clinicas.length > 1) {
        activeClinicaId.value = null
        if (response.user.role === 'recepcao') {
          navigateTo('/selecionar-clinica')
        } else {
          navigateTo('/selecionar-clinica')
        }
      } else {
        const primeira = response.clinicas[0]
        if (primeira) {
          activeClinicaId.value = primeira.id
        }
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
    activeClinicaId.value = null
    sessionChecked.value = true
    navigateTo('/login')
  }

  async function fetchUser() {
    if (user.value) return true

    try {
      const response = await $fetch<{ user: AuthUser, clinicas: Clinica[] }>('/api/auth/me')
      user.value = response.user
      clinicas.value = response.clinicas
      if (response.clinicas.length === 1) {
        activeClinicaId.value = response.clinicas[0]!.id
      }
      sessionChecked.value = true
      return true
    } catch {
      user.value = null
      clinicas.value = []
      activeClinicaId.value = null
      sessionChecked.value = true
      return false
    }
  }

  function setActiveClinica(id: number) {
    const clinicaId = normalizarClinicaId(id)
    if (!clinicaId || !clinicas.value.some(c => c.id === clinicaId)) return
    activeClinicaId.value = clinicaId
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
