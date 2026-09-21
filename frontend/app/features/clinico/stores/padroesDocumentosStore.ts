import { defineStore } from 'pinia'
import type { PadraoDocumentoMedico } from '../types'
import { atualizarPadraoDocumento, criarPadraoDocumento, deletarPadraoDocumento, listarPadroesDocumentos } from '../services/clinicoService'

export const usePadroesDocumentosStore = defineStore('padroesDocumentos', () => {
  const padroes = ref<PadraoDocumentoMedico[]>([])
  const loading = ref(false)

  async function fetchAll(medicoId?: number) {
    loading.value = true
    try {
      padroes.value = await listarPadroesDocumentos(medicoId)
    } catch {
      console.error('Erro ao carregar padrões de documentos médicos')
    } finally {
      loading.value = false
    }
  }

  async function criar(data: { nome: string, titulo: string, conteudo: string }, medicoId?: number) {
    const novo = await criarPadraoDocumento(data, medicoId)
    padroes.value.push(novo)
    return novo
  }

  async function atualizar(id: string, data: Partial<{ nome: string, titulo: string, conteudo: string }>, medicoId?: number) {
    const atualizado = await atualizarPadraoDocumento(id, data, medicoId)
    const index = padroes.value.findIndex(padrao => padrao.id === id)
    if (index !== -1) padroes.value[index] = atualizado
    return atualizado
  }

  async function deletar(id: string, medicoId?: number) {
    await deletarPadraoDocumento(id, medicoId)
    padroes.value = padroes.value.filter(padrao => padrao.id !== id)
  }

  return { padroes, loading, fetchAll, criar, atualizar, deletar }
})
