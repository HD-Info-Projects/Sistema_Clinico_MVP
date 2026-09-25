export const ROLES_USUARIO = [
  'medico',
  'recepcao',
  'coord_recepcao',
  'dpo',
  'ti',
  'admin',
  'coord_financeiro'
] as const

export type RoleUsuario = typeof ROLES_USUARIO[number]

export const RECEPCAO_ROLES: RoleUsuario[] = ['recepcao', 'coord_recepcao', 'admin']
export const COORD_RECEPCAO_ROLES: RoleUsuario[] = ['coord_recepcao', 'admin']
export const LGPD_ROLES: RoleUsuario[] = ['admin', 'dpo', 'ti']
export const MEDICO_ROLES: RoleUsuario[] = ['medico']
export const FINANCEIRO_ROLES: RoleUsuario[] = ['coord_financeiro', 'admin']
export const UNIDADE_REQUIRED_ROLES: RoleUsuario[] = ['medico', 'recepcao', 'coord_recepcao']

export const ROLE_OPTIONS: { label: string, value: RoleUsuario }[] = [
  { label: 'Medico', value: 'medico' },
  { label: 'Recepcao', value: 'recepcao' },
  { label: 'Coord. Recepcao', value: 'coord_recepcao' },
  { label: 'DPO', value: 'dpo' },
  { label: 'TI', value: 'ti' },
  { label: 'Administrador', value: 'admin' },
  { label: 'Coord. Financeiro', value: 'coord_financeiro' }
]

export function roleIn(role: string | null | undefined, roles: readonly RoleUsuario[]) {
  return roles.includes(role as RoleUsuario)
}

export function roleExigeUnidade(role: string | null | undefined) {
  return roleIn(role, UNIDADE_REQUIRED_ROLES)
}

export function roleLabel(role: string | null | undefined) {
  return ROLE_OPTIONS.find(option => option.value === role)?.label || role || 'Sem perfil'
}

export function roleColor(role: string | null | undefined) {
  switch (role) {
    case 'admin': return 'error'
    case 'medico': return 'primary'
    case 'recepcao': return 'success'
    case 'coord_recepcao': return 'warning'
    case 'dpo': return 'secondary'
    case 'ti': return 'info'
    case 'coord_financeiro': return 'tertiary'
    default: return 'neutral'
  }
}
