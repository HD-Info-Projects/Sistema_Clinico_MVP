import { defineStore } from 'pinia'
import type { Padrao, PadraoReceita, PadraoExame } from '~/types'

export const usePadroesStore = defineStore('padroes', () => {
  const padroes = ref<Padrao[]>([])
  const loading = ref(false)

  const receitas = computed(() => padroes.value.filter((p): p is PadraoReceita => p.tipo === 'receita'))
  const exames = computed(() => padroes.value.filter((p): p is PadraoExame => p.tipo === 'exame'))

  async function fetchAll(medicoId?: number) {
    loading.value = true
    try {
      padroes.value = await $fetch<Padrao[]>('/api/padroes', { params: medicoId ? { medicoId } : undefined })
    } catch {
      console.error('Erro ao carregar padrões')
    } finally {
      loading.value = false
    }
  }

  async function criar(data: { nome: string, tipo: string, [key: string]: unknown }, medicoId?: number) {
    const novo = await $fetch('/api/padroes', {
      method: 'POST',
      body: data,
      params: medicoId ? { medicoId } : undefined
    })
    padroes.value.push(novo as Padrao)
    return novo
  }

  async function atualizar(id: string, data: { nome?: string, [key: string]: unknown }, medicoId?: number) {
    const padrao = padroes.value.find(p => p.id === id)
    const atualizado = await $fetch(`/api/padroes/${id}`, {
      method: 'PATCH',
      body: { ...data, tipo: data.tipo || padrao?.tipo },
      params: medicoId ? { medicoId } : undefined
    })
    const idx = padroes.value.findIndex(p => p.id === id)
    if (idx !== -1) padroes.value[idx] = atualizado as Padrao
    return atualizado
  }

  async function deletar(id: string, medicoId?: number) {
    const padrao = padroes.value.find(p => p.id === id)
    await $fetch(`/api/padroes/${id}`, {
      method: 'DELETE',
      params: { tipo: padrao?.tipo, ...(medicoId ? { medicoId } : {}) }
    })
    padroes.value = padroes.value.filter(p => p.id !== id)
  }

  return {
    padroes,
    loading,
    receitas,
    exames,
    fetchAll,
    criar,
    atualizar,
    deletar
  }
})
