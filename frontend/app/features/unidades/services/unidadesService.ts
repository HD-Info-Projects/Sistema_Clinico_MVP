import type { Unidade, UnidadeForm } from '../types'

export type UnidadeResponse = {
  message?: string
  unidade?: Unidade
}

export function listarUnidades() {
  return $fetch<Unidade[]>('/api/unidades')
}

export function criarUnidade(form: UnidadeForm) {
  return $fetch<UnidadeResponse>('/api/unidades', {
    method: 'POST',
    body: form
  })
}

export function atualizarUnidade(id: number, form: Partial<UnidadeForm>) {
  return $fetch<UnidadeResponse>(`/api/unidades/${id}`, {
    method: 'PUT',
    body: form
  })
}

export function excluirUnidade(id: number) {
  return $fetch<UnidadeResponse>(`/api/unidades/${id}`, { method: 'DELETE' })
}
