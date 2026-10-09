import type { PagamentosConsulta, PagamentosResponse, PagamentosResumo } from '../types'
import { criarPagamentosMock } from '../mocks/pagamentos'
import { validarIntervaloPagamento } from '../utils/periodos'

function normalizarNome(nome: string) {
  return nome.normalize('NFD').replace(/[\u0300-\u036f]/g, '').trim().toLocaleLowerCase('pt-BR')
}

/** Replace the mock source with /api/financeiro/pagamentos when the API is available. */
export async function listarPagamentos(filtros: PagamentosConsulta, referencia = new Date()): Promise<PagamentosResponse> {
  if (!Number.isInteger(filtros.unidadeId) || filtros.unidadeId <= 0) {
    throw new Error('Selecione uma unidade para carregar os pagamentos.')
  }
  const erroPeriodo = validarIntervaloPagamento(filtros.dataIni, filtros.dataFim)
  if (erroPeriodo) throw new Error(erroPeriodo)
  if (!Number.isInteger(filtros.page) || filtros.page < 1 || !Number.isInteger(filtros.pageSize) || filtros.pageSize < 1) {
    throw new Error('Paginação inválida.')
  }

  const paciente = normalizarNome(filtros.paciente || '')
  const cpf = (filtros.cpf || '').replace(/\D/g, '')
  const filtrados = criarPagamentosMock(filtros.unidadeId, referencia)
    .filter(item => item.unidadeId === filtros.unidadeId
      && item.data >= filtros.dataIni && item.data <= filtros.dataFim
      && (!paciente || normalizarNome(item.paciente.nome).includes(paciente))
      && (!cpf || item.paciente.cpf.includes(cpf))
      && (!filtros.status || item.status === filtros.status))
    .sort((a, b) => b.data.localeCompare(a.data) || a.id.localeCompare(b.id, 'pt-BR', { numeric: true }))

  const resumo: PagamentosResumo = {
    conciliados: 0,
    pendentes: 0,
    divergentes: 0,
    totalBrutoCentavos: 0
  }
  for (const item of filtrados) {
    if (item.status === 'conciliado') resumo.conciliados++
    else if (item.status === 'pendente') resumo.pendentes++
    else resumo.divergentes++
    resumo.totalBrutoCentavos += item.valorBrutoCentavos
  }

  const ultimaPagina = Math.max(1, Math.ceil(filtrados.length / filtros.pageSize))
  const page = Math.min(filtros.page, ultimaPagina)
  const inicio = (page - 1) * filtros.pageSize
  return {
    items: filtrados.slice(inicio, inicio + filtros.pageSize),
    total: filtrados.length,
    page,
    pageSize: filtros.pageSize,
    resumo
  }
}
