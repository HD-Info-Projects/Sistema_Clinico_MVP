import { defineStore } from 'pinia'
import type { MedicoSpdata, RoleUsuario, Usuario, UsuarioForm } from '../types'
import {
  atualizarUsuario,
  buscarMedicosSpdataUsuarios,
  criarUsuario,
  desbloquearUsuario,
  excluirUsuario,
  listarUsuarios
} from '../services/usuariosService'

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
      const data = await listarUsuarios(role)
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
      const data = await criarUsuario(form)
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
      const data = await atualizarUsuario(id, form)
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
      const data = await excluirUsuario(id)
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

  async function desbloquear(id: number) {
    loading.value = true
    error.value = null
    try {
      const data = await desbloquearUsuario(id)
      if (data.usuario) {
        const index = usuarios.value.findIndex(u => u.id === id)
        if (index !== -1) usuarios.value[index] = data.usuario
      }
      return { success: true, message: data.message || 'Usuário desbloqueado com sucesso' }
    } catch (e) {
      const message = mensagemErro(e, 'Erro ao desbloquear usuario')
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
      const data = await buscarMedicosSpdataUsuarios(filtros)
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
    desbloquear,
    excluir,
    buscarMedicosSpdata,
    limparMedicosSpdata,
    porRole
  }
})
