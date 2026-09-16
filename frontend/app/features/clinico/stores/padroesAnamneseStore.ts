import { defineStore } from 'pinia'
import type { PadraoAnamnese, PadraoTextoPayload } from '../types'
import { atualizarPadraoAnamnese, criarPadraoAnamnese, deletarPadraoAnamnese, listarPadroesAnamnese } from '../services/clinicoService'

export const usePadroesAnamneseStore = defineStore('padroesAnamnese', () => {
  const padroes = ref<PadraoAnamnese[]>([])
  const loading = ref(false)

  async function fetchAll(medicoId?: number) {
    loading.value = true
    try {
      padroes.value = await listarPadroesAnamnese(medicoId)
    } catch {
      console.error('Erro ao carregar padrões de anamnese')
    } finally {
      loading.value = false
    }
  }

  async function criar(data: PadraoTextoPayload, medicoId?: number) {
    const novo = await criarPadraoAnamnese(data, medicoId)
    padroes.value.push(novo)
    return novo
  }

  async function atualizar(id: string, data: Partial<PadraoTextoPayload>, medicoId?: number) {
    const atualizado = await atualizarPadraoAnamnese(id, data, medicoId)
    const idx = padroes.value.findIndex(p => p.id === id)
    if (idx !== -1) padroes.value[idx] = atualizado
    return atualizado
  }

  async function deletar(id: string, medicoId?: number) {
    await deletarPadraoAnamnese(id, medicoId)
    padroes.value = padroes.value.filter(p => p.id !== id)
  }

  return { padroes, loading, fetchAll, criar, atualizar, deletar }
})
