import type { H3Event } from 'h3'
import type { Paciente } from '~/types'
import { flaskFetch } from '../../utils/flask'
import { getActiveClinicaId } from '../../utils/clinicas'

type FetchLikeError = {
  status?: number
  statusCode?: number
  response?: { status?: number }
}

function statusFetch(error: unknown): number | undefined {
  if (!error || typeof error !== 'object') return undefined
  const fetchError = error as FetchLikeError
  return fetchError.statusCode ?? fetchError.status ?? fetchError.response?.status
}

function campoTexto(item: Record<string, unknown>, nome: string) {
  const valor = item[nome]
  return valor === null || valor === undefined ? '' : String(valor)
}

function campoData(item: Record<string, unknown>, nome: string): string | null {
  const valor = item[nome]
  return valor === null || valor === undefined || valor === '' ? null : String(valor)
}

function normalizarPaciente(item: Record<string, unknown>): Paciente {
  return {
    id: Number(item.ID_PACIENTE) || 0,
    nome: campoTexto(item, 'PACIENTE'),
    encaixado: false,
    sexo: campoTexto(item, 'SEXO') === 'F' ? 'feminino' : 'masculino',
    dataNascimento: campoData(item, 'DATA_NASCIMENTO'),
    tipoSanguineo: '',
    alergias: [],
    medicamentosEmUso: [],
    convenio: campoTexto(item, 'ID_TBCONVEN'),
    idConvenioSpdata: Number(item.ID_TBCONVEN) || null,
    telefone: campoTexto(item, 'CELULAR'),
    email: campoTexto(item, 'EMAIL'),
    cpf: campoTexto(item, 'CPF'),
    endereco: campoTexto(item, 'ENDERECO'),
    historicoRecente: []
  }
}

export function normalizarCpf(valor: unknown): string | undefined {
  const texto = String(valor || '').trim()
  const semDecimal = texto.endsWith('.0') && [10, 11].includes(texto.slice(0, -2).replace(/\D/g, '').length)
    ? texto.slice(0, -2)
    : texto
  const digitos = semDecimal.replace(/\D/g, '')
  const cpf = digitos.length === 10 ? digitos.padStart(11, '0') : digitos

  if (cpf.length !== 11) return undefined
  if (new Set(cpf).size === 1) return undefined

  return cpf
}

function clampLimit(limit: number, fallback = 10) {
  return Number.isFinite(limit) ? Math.min(Math.max(limit, 1), 50) : fallback
}

function clampOffset(offset: number) {
  return Number.isFinite(offset) ? Math.max(offset, 0) : 0
}

function responseVaziaHistorico(limit: number, offset: number): { items: [], limit: number, offset: number, has_more: false } {
  return { items: [], limit, offset, has_more: false }
}

export async function listarPacientes(event: H3Event, query: Record<string, unknown>) {
  const search = query.search ? String(query.search) : ''
  const data = query.data ? String(query.data) : ''
  const params = new URLSearchParams()
  if (data) params.set('data', data)

  const raw = await flaskFetch<Record<string, unknown>[]>(event, `/dashboard/pacientes${params.toString() ? `?${params.toString()}` : ''}`)
  const pacientes = raw.map(normalizarPaciente)

  if (!search.trim()) return pacientes

  const termo = search.trim().toLocaleLowerCase('pt-BR')
  return pacientes.filter(p => p.nome.toLocaleLowerCase('pt-BR').includes(termo))
}

export async function listarPacientesFila(event: H3Event) {
  const clinicaId = getActiveClinicaId(event) ?? 0
  const raw = await flaskFetch<Record<string, unknown>[]>(event, '/dashboard/pacientes')

  return raw.map((item: Record<string, unknown>) => {
    const entrada = item.DATA_HORA_ENTRADA ? new Date(String(item.DATA_HORA_ENTRADA)) : new Date()
    const dataStr = entrada.toISOString().slice(0, 10)
    const horarioStr = entrada.toISOString().slice(11, 16)

    return {
      id: Number(item.COD_ATENDIMENTO) || 0,
      pacienteId: Number(item.ID_PACIENTE) || 0,
      medicoId: Number(item.ID_MEDICO) || 0,
      clinicaId,
      data: dataStr,
      horario: horarioStr,
      prioridade: 'normal',
      status: 'em-espera',
      descricao: '',
      criadoEm: dataStr,
      paciente: {
        id: Number(item.ID_PACIENTE) || null,
        nome: String(item.PACIENTE || ''),
        sexo: String(item.SEXO) === 'F' ? 'feminino' : 'masculino',
        dataNascimento: campoData(item, 'DATA_NASCIMENTO'),
        tipoSanguineo: '',
        alergias: [],
        medicamentosEmUso: [],
        convenio: String(item.ID_TBCONVEN),
        telefone: String(item.CELULAR || ''),
        email: String(item.EMAIL || 'Não Informado'),
        cpf: String(item.CPF || ''),
        endereco: String(item.ENDERECO || ''),
        historicoRecente: []
      }
    }
  })
}

export async function buscarHistoricoLocal(event: H3Event, id: string, query: Record<string, unknown>) {
  const params = new URLSearchParams()

  if (query.cpf) params.set('cpf', String(query.cpf))
  if (query.nome) params.set('nome', String(query.nome))
  if (query.spdataAtendimentoId) params.set('spdataAtendimentoId', String(query.spdataAtendimentoId))
  if (query.data) params.set('data', String(query.data))

  const qs = params.toString()
  try {
    return await flaskFetch(event, `/prontuario/historico-local/${id}${qs ? `?${qs}` : ''}`)
  } catch (error) {
    if (statusFetch(error) === 404) return []
    throw error
  }
}

export async function buscarHistoricoPaciente(event: H3Event, id: string, query: Record<string, unknown>) {
  const params = new URLSearchParams()
  const cpf = normalizarCpf(query.cpf)
  const limit = clampLimit(Number(query.limit || 10))
  const offset = clampOffset(Number(query.offset || 0))

  if (cpf) params.set('cpf', cpf)
  if (query.nome) params.set('nome', String(query.nome))
  if (query.spdataAtendimentoId) params.set('spdataAtendimentoId', String(query.spdataAtendimentoId))
  params.set('limit', String(limit))
  params.set('offset', String(offset))

  const qs = params.toString()
  try {
    return await flaskFetch(event, `/prontuario/historico-paciente/${id}${qs ? `?${qs}` : ''}`)
  } catch (error) {
    if (statusFetch(error) === 404) return responseVaziaHistorico(limit, offset)
    throw error
  }
}

export async function buscarHistoricoSpdata(event: H3Event, id: string, query: Record<string, unknown>) {
  const params = new URLSearchParams()
  const cpf = normalizarCpf(query.cpf)
  const limit = clampLimit(Number(query.limit || 10))
  const offset = clampOffset(Number(query.offset || 0))

  if (cpf) params.set('cpf', cpf)
  if (query.nome) params.set('nome', String(query.nome))
  if (query.spdataAtendimentoId) params.set('spdataAtendimentoId', String(query.spdataAtendimentoId))
  params.set('limit', String(limit))
  params.set('offset', String(offset))

  const qs = params.toString()
  try {
    return await flaskFetch(event, `/prontuario/historico-spdata/${id}${qs ? `?${qs}` : ''}`)
  } catch (error) {
    if (statusFetch(error) === 404) return responseVaziaHistorico(limit, offset)
    throw error
  }
}

export async function buscarCid(event: H3Event, query: Record<string, unknown>) {
  const params = new URLSearchParams()

  const q = String(query.q || '').trim()
  const requestedLimit = Number(query.limit || 20)
  const requestedOffset = Number(query.offset || 0)
  const limit = Number.isFinite(requestedLimit) ? requestedLimit : 20
  const offset = Number.isFinite(requestedOffset) ? requestedOffset : 0

  if (q) params.set('q', q)
  params.set('limit', String(Math.min(Math.max(limit, 1), 50)))
  params.set('offset', String(Math.max(offset, 0)))

  const qs = params.toString()
  const raw = await flaskFetch<{ items: Record<string, unknown>[] }>(
    event,
    `/prontuario/doenca-cid?${qs}`,
    { activeClinica: false }
  )

  return raw.items.map((item: Record<string, unknown>) => ({
    cid: item.CID,
    nome: item.DOENCA
  }))
}
