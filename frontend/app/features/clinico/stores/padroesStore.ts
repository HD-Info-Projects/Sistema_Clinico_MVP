import { defineStore } from 'pinia'
import type { Padrao, PadraoExame, PadraoReceita, PadraoPayload } from '../types'
import { atualizarPadrao, criarPadrao, deletarPadrao, listarPadroes } from '../services/clinicoService'

export const usePadroesStore = defineStore('padroes', () => {
  const padroes = ref<Padrao[]>([])
  const loading = ref(false)

  const receitas = computed(() => padroes.value.filter((p): p is PadraoReceita => p.tipo === 'receita'))
  const exames = computed(() => padroes.value.filter((p): p is PadraoExame => p.tipo === 'exame'))

  async function fetchAll(medicoId?: number) {
    loading.value = true
    try {
      padroes.value = await listarPadroes(medicoId)
    } catch {
      console.error('Erro ao carregar padrões')
    } finally {
      loading.value = false
    }
  }

  async function criar(data: PadraoPayload, medicoId?: number) {
    const novo = await criarPadrao(data, medicoId)
    padroes.value.push(novo)
    return novo
  }

  async function atualizar(id: string, data: { nome?: string, [key: string]: unknown }, medicoId?: number) {
    const padrao = padroes.value.find(p => p.id === id)
    const atualizado = await atualizarPadrao(id, { ...data, tipo: data.tipo || padrao?.tipo }, medicoId)
    const idx = padroes.value.findIndex(p => p.id === id)
    if (idx !== -1) padroes.value[idx] = atualizado
    return atualizado
  }

  async function deletar(id: string, medicoId?: number) {
    const padrao = padroes.value.find(p => p.id === id)
    await deletarPadrao(id, padrao?.tipo, medicoId)
    padroes.value = padroes.value.filter(p => p.id !== id)
  }

  return { padroes, loading, receitas, exames, fetchAll, criar, atualizar, deletar }
})
