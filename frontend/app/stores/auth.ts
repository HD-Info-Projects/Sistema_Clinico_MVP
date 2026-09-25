import { defineStore } from 'pinia'
import { buscarSessaoAuth, loginAuth, logoutAuth } from '~/features/auth/services/authService'
import type { AuthSessionResponse, AuthUser, Clinica } from '~/features/auth/types'
import { LGPD_ROLES, MEDICO_ROLES, RECEPCAO_ROLES, roleIn } from '~/utils/roles'

export type AccessMode = 'recepcionista' | 'administrador' | 'logs'

const MODOS_ACESSO: AccessMode[] = ['recepcionista', 'administrador', 'logs']

function modoValido(valor: unknown): AccessMode | null {
  return MODOS_ACESSO.includes(valor as AccessMode) ? (valor as AccessMode) : null
}

export function paginaInicialPorModo(modo: AccessMode | null) {
  switch (modo) {
    case 'recepcionista': return '/recepcao'
    case 'administrador': return '/admin'
    case 'logs': return '/lgpd/auditoria'
    default: return '/selecionar-acesso'
  }
}

export const useAuthStore = defineStore('auth', () => {
  const config = useRuntimeConfig()
  const accessModeCookieMaxAgeSeconds = Number(config.public.authCookieMaxAgeSeconds) || 60 * 60 * 24 * 7

  const user = ref<AuthUser | null>(null)
  const clinicas = ref<Clinica[]>([])
  const sessionChecked = ref(false)

  const isLoggedIn = computed(() => !!user.value)

  function normalizarClinicaId(value: unknown) {
    const id = Number(value)
    return Number.isInteger(id) && id > 0 ? id : null
  }

  const _accessModeCookie = useCookie<string | null>('access_mode', {
    maxAge: accessModeCookieMaxAgeSeconds,
    sameSite: 'strict',
    path: '/'
  })

  const accessMode = computed<AccessMode | null>(() => modoValido(_accessModeCookie.value))

  function setAccessMode(modo: AccessMode) {
    _accessModeCookie.value = modo
  }

  function limparAccessMode() {
    _accessModeCookie.value = null
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

  const isMedico = computed(() => roleIn(user.value?.role, MEDICO_ROLES))
  const isRecepcao = computed(() => roleIn(user.value?.role, RECEPCAO_ROLES))
  const isAdmin = computed(() => user.value?.role === 'admin')
  const canAccessLgpd = computed(() => roleIn(user.value?.role, LGPD_ROLES))

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
      const response = await loginAuth(credentials)

      aplicarSessao(response)

      if (response.user.role === 'admin') {
        navigateTo('/selecionar-acesso')
      } else if (roleIn(response.user.role, LGPD_ROLES)) {
        navigateTo('/lgpd/auditoria')
      } else if ((roleIn(response.user.role, RECEPCAO_ROLES) || roleIn(response.user.role, MEDICO_ROLES)) && response.clinicas.length > 1 && !activeClinicaId.value) {
        navigateTo('/selecionar-clinica')
      } else if (roleIn(response.user.role, RECEPCAO_ROLES)) {
        navigateTo('/recepcao')
      } else if (roleIn(response.user.role, MEDICO_ROLES)) {
        navigateTo('/dashboard')
      } else {
        navigateTo('/acesso-negado')
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
      await logoutAuth()
    } catch {
      // A limpeza local ainda deve ocorrer se o servidor já encerrou a sessão.
    }

    user.value = null
    clinicas.value = []
    selecionarClinicaAtiva(null)
    limparAccessMode()
    sessionChecked.value = true
    navigateTo('/login')
  }

  async function fetchUser() {
    if (user.value) return true

    try {
      const response = await buscarSessaoAuth()
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
    isAdmin,
    canAccessLgpd,
    accessMode,
    setAccessMode,
    limparAccessMode,
    login,
    logout,
    fetchUser,
    setActiveClinica
  }
})
