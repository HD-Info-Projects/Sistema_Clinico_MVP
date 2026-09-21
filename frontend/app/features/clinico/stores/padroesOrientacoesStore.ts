import { defineStore } from 'pinia'
import type { PadraoOrientacaoExame, PadraoTextoPayload } from '../types'
import { atualizarPadraoOrientacao, criarPadraoOrientacao, deletarPadraoOrientacao, listarPadroesOrientacoes } from '../services/clinicoService'

export const usePadroesOrientacoesStore = defineStore('padroesOrientacoes', () => {
  const padroes = ref<PadraoOrientacaoExame[]>([])
  const loading = ref(false)

  async function fetchAll(medicoId?: number) {
    loading.value = true
    try {
      padroes.value = await listarPadroesOrientacoes(medicoId)
    } catch {
      console.error('Erro ao carregar padrões de orientação')
    } finally {
      loading.value = false
    }
  }

  async function criar(data: PadraoTextoPayload, medicoId?: number) {
    const novo = await criarPadraoOrientacao(data, medicoId)
    padroes.value.push(novo)
    return novo
  }

  async function atualizar(id: string, data: Partial<PadraoTextoPayload>, medicoId?: number) {
    const atualizado = await atualizarPadraoOrientacao(id, data, medicoId)
    const idx = padroes.value.findIndex(p => p.id === id)
    if (idx !== -1) padroes.value[idx] = atualizado
    return atualizado
  }

  async function deletar(id: string, medicoId?: number) {
    await deletarPadraoOrientacao(id, medicoId)
    padroes.value = padroes.value.filter(p => p.id !== id)
  }

  return { padroes, loading, fetchAll, criar, atualizar, deletar }
})
