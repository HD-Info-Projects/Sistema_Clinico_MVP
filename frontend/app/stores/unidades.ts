import { defineStore } from 'pinia'
import type { Unidade, UnidadeForm } from '~/types'

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
      error.value = 'Erro ao carregar unidades'
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
      const data = await $fetch<Unidade>('/api/unidades', {
        method: 'POST',
        body: form
      })
      unidades.value.push(data)
      return { success: true }
    } catch (e) {
      error.value = 'Erro ao criar unidade'
      console.error(e)
      return { success: false, message: 'Erro ao criar unidade' }
    } finally {
      loading.value = false
    }
  }

  async function atualizar(id: number, form: Partial<UnidadeForm>) {
    loading.value = true
    error.value = null
    try {
      const data = await $fetch<Unidade>(`/api/unidades/${id}`, {
        method: 'PUT',
        body: form
      })
      const index = unidades.value.findIndex(u => u.id === id)
      if (index !== -1) unidades.value[index] = data
      return { success: true }
    } catch (e) {
      error.value = 'Erro ao atualizar unidade'
      console.error(e)
      return { success: false, message: 'Erro ao atualizar unidade' }
    } finally {
      loading.value = false
    }
  }

  async function excluir(id: number) {
    loading.value = true
    error.value = null
    try {
      await $fetch(`/api/unidades/${id}`, { method: 'DELETE' })
      unidades.value = unidades.value.filter(u => u.id !== id)
      return { success: true }
    } catch (e) {
      error.value = 'Erro ao excluir unidade'
      console.error(e)
      return { success: false, message: 'Erro ao excluir unidade' }
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