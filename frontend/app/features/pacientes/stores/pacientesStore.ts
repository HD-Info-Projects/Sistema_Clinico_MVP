import { defineStore } from 'pinia'
import type { Paciente } from '../types'
import { listarPacientes } from '../services/pacientesService'

export const usePacientesStore = defineStore('pacientes', () => {
  const pacientes = ref<Paciente[]>([])
  const loading = ref(false)

  async function fetchPacientes(search?: string) {
    loading.value = true
    try {
      pacientes.value = await listarPacientes(search ? { search } : undefined)
    } catch {
      console.error('Erro ao carregar pacientes')
    } finally {
      loading.value = false
    }
  }

  function getPacienteById(id: number) {
    return pacientes.value.find(p => p.id === id) ?? null
  }

  return {
    pacientes,
    loading,
    fetchPacientes,
    getPacienteById
  }
})
