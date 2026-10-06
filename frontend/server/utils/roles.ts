export const SERVER_ROLES_USUARIO = [
  'medico',
  'assistente',
  'recepcao',
  'coord_recepcao',
  'dpo',
  'admin',
  'coord_financeiro'
] as const

export type ServerRoleUsuario = typeof SERVER_ROLES_USUARIO[number]

export const SERVER_MEDICO_ROLES: ServerRoleUsuario[] = ['medico']
export const SERVER_ASSISTENTE_ROLES: ServerRoleUsuario[] = ['assistente', 'admin']
export const SERVER_RECEPCAO_ROLES: ServerRoleUsuario[] = ['recepcao', 'coord_recepcao', 'admin']
export const SERVER_COORD_RECEPCAO_ROLES: ServerRoleUsuario[] = ['coord_recepcao', 'admin']
export const SERVER_LGPD_ROLES: ServerRoleUsuario[] = ['dpo', 'admin']
export const SERVER_CHAMADAS_ROLES: ServerRoleUsuario[] = ['medico', 'assistente', 'recepcao', 'coord_recepcao', 'admin']
export const SERVER_UNIDADE_REQUIRED_ROLES: ServerRoleUsuario[] = ['medico', 'assistente', 'recepcao', 'coord_recepcao']
