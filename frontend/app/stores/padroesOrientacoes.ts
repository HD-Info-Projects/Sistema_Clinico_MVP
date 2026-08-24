import { defineStore } from 'pinia'
import type { PadraoOrientacaoExame } from '~/types'

export const usePadroesOrientacoesStore = defineStore('padroesOrientacoes', () => {
  const padroes = ref<PadraoOrientacaoExame[]>([])
  const loading = ref(false)

  async function fetchAll(medicoId?: number) {
    loading.value = true
    try {
      padroes.value = await $fetch<PadraoOrientacaoExame[]>('/api/padroes-orientacoes', { params: medicoId ? { medicoId } : undefined })
    } catch {
      console.error('Erro ao carregar padrões de orientação')
    } finally {
      loading.value = false
    }
  }

  async function criar(data: { nome: string, conteudo: string }, medicoId?: number) {
    const novo = await $fetch<PadraoOrientacaoExame>('/api/padroes-orientacoes', {
      method: 'POST',
      body: data,
      params: medicoId ? { medicoId } : undefined
    })
    padroes.value.push(novo)
    return novo
  }

  async function atualizar(id: string, data: { nome?: string, conteudo?: string }, medicoId?: number) {
    const atualizado = await $fetch<PadraoOrientacaoExame>(`/api/padroes-orientacoes/${id}`, {
      method: 'PATCH',
      body: data,
      params: medicoId ? { medicoId } : undefined
    })
    const idx = padroes.value.findIndex(p => p.id === id)
    if (idx !== -1) padroes.value[idx] = atualizado
    return atualizado
  }

  async function deletar(id: string, medicoId?: number) {
    await $fetch(`/api/padroes-orientacoes/${id}`, {
      method: 'DELETE',
      params: medicoId ? { medicoId } : undefined
    })
    padroes.value = padroes.value.filter(p => p.id !== id)
  }

  return {
    padroes,
    loading,
    fetchAll,
    criar,
    atualizar,
    deletar
  }
})
