import type { Paciente } from '~/types'

function campoTexto(item: Record<string, unknown>, nome: string) {
  const valor = item[nome]
  return valor === null || valor === undefined ? '' : String(valor)
}

function normalizarPaciente(item: Record<string, unknown>): Paciente {
  return {
    id: Number(item.ID_PACIENTE) || 0,
    nome: campoTexto(item, 'PACIENTE'),
    encaixado: false,
    sexo: campoTexto(item, 'SEXO') === 'F' ? 'feminino' : 'masculino',
    dataNascimento: campoTexto(item, 'DATA_NASCIMENTO'),
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

export default defineEventHandler(async (event) => {
  const query = getQuery(event)
  const search = query.search ? String(query.search) : ''
  const data = query.data ? String(query.data) : ''
  const params = new URLSearchParams()
  if (data) params.set('data', data)

  try {
    const raw = await flaskFetch<Record<string, unknown>[]>(event, `/dashboard/pacientes${params.toString() ? `?${params.toString()}` : ''}`)
    const pacientes = raw.map(normalizarPaciente)

    if (!search.trim()) return pacientes

    const termo = search.trim().toLocaleLowerCase('pt-BR')
    return pacientes.filter(p => p.nome.toLocaleLowerCase('pt-BR').includes(termo))
  } catch (error) {
    throwProxyError(error, 'Falha ao carregar pacientes no backend Flask')
  }
})
