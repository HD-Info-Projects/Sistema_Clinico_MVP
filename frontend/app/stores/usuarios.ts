import { defineStore } from 'pinia'
import type { Usuario, UsuarioForm, RoleUsuario } from '~/types'

export const useUsuariosStore = defineStore('usuarios', () => {
  const usuarios = ref<Usuario[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)

  async function fetchAll(role?: RoleUsuario) {
    loading.value = true
    error.value = null
    try {
      const query = role ? `?role=${role}` : ''
      const data = await $fetch<Usuario[]>(`/api/usuarios${query}`)
      usuarios.value = data
    } catch (e) {
      error.value = 'Erro ao carregar usuarios'
      console.error(e)
      usuarios.value = []
    } finally {
      loading.value = false
    }
  }

  async function criar(form: UsuarioForm) {
    loading.value = true
    error.value = null
    try {
      const data = await $fetch<Usuario>('/api/usuarios', {
        method: 'POST',
        body: form
      })
      usuarios.value.push(data)
      return { success: true }
    } catch (e) {
      error.value = 'Erro ao criar usuario'
      console.error(e)
      return { success: false, message: 'Erro ao criar usuario' }
    } finally {
      loading.value = false
    }
  }

  async function atualizar(id: number, form: Partial<UsuarioForm>) {
    loading.value = true
    error.value = null
    try {
      const data = await $fetch<Usuario>(`/api/usuarios/${id}`, {
        method: 'PUT',
        body: form
      })
      const index = usuarios.value.findIndex(u => u.id === id)
      if (index !== -1) usuarios.value[index] = data
      return { success: true }
    } catch (e) {
      error.value = 'Erro ao atualizar usuario'
      console.error(e)
      return { success: false, message: 'Erro ao atualizar usuario' }
    } finally {
      loading.value = false
    }
  }

  async function excluir(id: number) {
    loading.value = true
    error.value = null
    try {
      await $fetch(`/api/usuarios/${id}`, { method: 'DELETE' })
      usuarios.value = usuarios.value.filter(u => u.id !== id)
      return { success: true }
    } catch (e) {
      error.value = 'Erro ao excluir usuario'
      console.error(e)
      return { success: false, message: 'Erro ao excluir usuario' }
    } finally {
      loading.value = false
    }
  }

  function porRole(role: RoleUsuario) {
    return usuarios.value.filter(u => u.role === role)
  }

  return {
    usuarios,
    loading,
    error,
    fetchAll,
    criar,
    atualizar,
    excluir,
    porRole
  }
})
