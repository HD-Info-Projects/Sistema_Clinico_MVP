import { defineStore } from 'pinia'
import type { Usuario, UsuarioForm, RoleUsuario, MedicoSpdata } from '~/types'

type UsuarioResponse = {
  message?: string
  usuario?: Usuario
}

function mensagemErro(error: unknown, fallback: string) {
  const err = error as {
    data?: {
      message?: string
      error?: string
      statusMessage?: string
      data?: { message?: string, error?: string }
    }
    statusMessage?: string
    message?: string
  }

  return err.data?.message
    || err.data?.error
    || err.data?.data?.message
    || err.data?.data?.error
    || err.data?.statusMessage
    || err.statusMessage
    || fallback
}

export const useUsuariosStore = defineStore('usuarios', () => {
  const usuarios = ref<Usuario[]>([])
  const medicosSpdata = ref<MedicoSpdata[]>([])
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
      error.value = mensagemErro(e, 'Erro ao carregar usuarios')
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
      const data = await $fetch<UsuarioResponse>('/api/usuarios', {
        method: 'POST',
        body: form
      })
      const usuario = data.usuario
      if (usuario) {
        const index = usuarios.value.findIndex(u => u.id === usuario.id)
        if (index !== -1) usuarios.value[index] = usuario
        else usuarios.value.push(usuario)
      }
      return { success: true, message: data.message || 'Usuário criado com sucesso' }
    } catch (e) {
      const message = mensagemErro(e, 'Erro ao criar usuario')
      error.value = message
      console.error(e)
      return { success: false, message }
    } finally {
      loading.value = false
    }
  }

  async function atualizar(id: number, form: Partial<UsuarioForm>) {
    loading.value = true
    error.value = null
    try {
      const data = await $fetch<UsuarioResponse>(`/api/usuarios/${id}`, {
        method: 'PUT',
        body: form
      })
      if (data.usuario) {
        const index = usuarios.value.findIndex(u => u.id === id)
        if (index !== -1) usuarios.value[index] = data.usuario
      }
      return { success: true, message: data.message || 'Usuário atualizado com sucesso' }
    } catch (e) {
      const message = mensagemErro(e, 'Erro ao atualizar usuario')
      error.value = message
      console.error(e)
      return { success: false, message }
    } finally {
      loading.value = false
    }
  }

  async function excluir(id: number) {
    loading.value = true
    error.value = null
    try {
      const data = await $fetch<UsuarioResponse>(`/api/usuarios/${id}`, { method: 'DELETE' })
      if (data.usuario) {
        const index = usuarios.value.findIndex(u => u.id === id)
        if (index !== -1) usuarios.value[index] = data.usuario
      }
      return { success: true, message: data.message || 'Usuário inativado com sucesso' }
    } catch (e) {
      const message = mensagemErro(e, 'Erro ao inativar usuario')
      error.value = message
      console.error(e)
      return { success: false, message }
    } finally {
      loading.value = false
    }
  }

  async function buscarMedicosSpdata(filtros: { spdata_id?: number | string, cpf?: string, nome?: string }) {
    loading.value = true
    error.value = null
    try {
      const params = new URLSearchParams()
      if (filtros.spdata_id) params.set('spdata_id', String(filtros.spdata_id))
      if (filtros.cpf) params.set('cpf', filtros.cpf)
      if (filtros.nome) params.set('nome', filtros.nome)

      const data = await $fetch<MedicoSpdata[]>(`/api/usuarios/medicos-spdata?${params.toString()}`)
      medicosSpdata.value = data
      return { success: true, data }
    } catch (e) {
      const message = mensagemErro(e, 'Erro ao buscar médicos no SPDATA')
      error.value = message
      console.error(e)
      medicosSpdata.value = []
      return { success: false, message, data: [] as MedicoSpdata[] }
    } finally {
      loading.value = false
    }
  }

  function porRole(role: RoleUsuario) {
    return usuarios.value.filter(u => u.role === role)
  }

  function limparMedicosSpdata() {
    medicosSpdata.value = []
  }

  return {
    usuarios,
    medicosSpdata,
    loading,
    error,
    fetchAll,
    criar,
    atualizar,
    excluir,
    buscarMedicosSpdata,
    limparMedicosSpdata,
    porRole
  }
})
