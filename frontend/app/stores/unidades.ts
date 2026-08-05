import { defineStore } from 'pinia'
import type { Unidade, UnidadeForm } from '~/types'

type UnidadeResponse = {
  message?: string
  unidade?: Unidade
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
  }

  return err.data?.message
    || err.data?.error
    || err.data?.data?.message
    || err.data?.data?.error
    || err.data?.statusMessage
    || err.statusMessage
    || fallback
}

export const useUnidadesStore = defineStore('unidades', () => {
  const unidades = ref<Unidade[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)

  async function fetchAll() {
    loading.value = true
    error.value = null
    try {
      const data = await $fetch<Unidade[]>('/api/unidades')
      unidades.value = data
    } catch (e) {
      error.value = mensagemErro(e, 'Erro ao carregar unidades')
      console.error(e)
      unidades.value = []
    } finally {
      loading.value = false
    }
  }

  async function criar(form: UnidadeForm) {
    loading.value = true
    error.value = null
    try {
      const data = await $fetch<UnidadeResponse>('/api/unidades', {
        method: 'POST',
        body: form
      })
      if (data.unidade) unidades.value.push(data.unidade)
      return { success: true, message: data.message || 'Unidade criada com sucesso' }
    } catch (e) {
      const message = mensagemErro(e, 'Erro ao criar unidade')
      error.value = message
      console.error(e)
      return { success: false, message }
    } finally {
      loading.value = false
    }
  }

  async function atualizar(id: number, form: Partial<UnidadeForm>) {
    loading.value = true
    error.value = null
    try {
      const data = await $fetch<UnidadeResponse>(`/api/unidades/${id}`, {
        method: 'PUT',
        body: form
      })
      if (data.unidade) {
        const index = unidades.value.findIndex(u => u.id === id)
        if (index !== -1) unidades.value[index] = data.unidade
      }
      return { success: true, message: data.message || 'Unidade atualizada com sucesso' }
    } catch (e) {
      const message = mensagemErro(e, 'Erro ao atualizar unidade')
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
      const data = await $fetch<UnidadeResponse>(`/api/unidades/${id}`, { method: 'DELETE' })
      if (data.unidade) {
        const index = unidades.value.findIndex(u => u.id === id)
        if (index !== -1) unidades.value[index] = data.unidade
      }
      return { success: true, message: data.message || 'Unidade inativada com sucesso' }
    } catch (e) {
      const message = mensagemErro(e, 'Erro ao inativar unidade')
      error.value = message
      console.error(e)
      return { success: false, message }
    } finally {
      loading.value = false
    }
  }

  return {
    unidades,
    loading,
    error,
    fetchAll,
    criar,
    atualizar,
    excluir
  }
})
