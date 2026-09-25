export const SERVER_ROLES_USUARIO = [
  'medico',
  'recepcao',
  'coord_recepcao',
  'dpo',
  'ti',
  'admin',
  'coord_financeiro'
] as const

export type ServerRoleUsuario = typeof SERVER_ROLES_USUARIO[number]

export const SERVER_RECEPCAO_ROLES: ServerRoleUsuario[] = ['recepcao', 'coord_recepcao', 'admin']
export const SERVER_CHAMADAS_ROLES: ServerRoleUsuario[] = ['medico', 'recepcao', 'coord_recepcao', 'admin']
export const SERVER_UNIDADE_REQUIRED_ROLES: ServerRoleUsuario[] = ['medico', 'recepcao', 'coord_recepcao']
