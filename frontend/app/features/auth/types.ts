import type { AuthUser, Clinica } from '~/types'

export type { AuthUser, Clinica }

export type AuthSessionResponse = {
  user: AuthUser
  clinicas: Clinica[]
  activeClinicaId?: number | null
}
