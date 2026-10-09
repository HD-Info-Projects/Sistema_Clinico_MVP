import type { FormaPagamento, Pagamento, PagamentoStatus } from '../types'
import { dataCalendario } from '../utils/periodos'

const nomes = [
  'Ana Silva', 'Bruno Costa', 'Carla Lima', 'Diego Rocha',
  'Elisa Santos', 'Felipe Alves', 'Gabriela Souza', 'Henrique Melo',
  'Isabela Martins', 'João Pereira', 'Larissa Oliveira', 'Marcos Ribeiro'
]

const atendimentos = ['Consulta cardiológica', 'Ultrassonografia', 'Consulta clínica geral', 'Curativo ambulatorial']
const formas: FormaPagamento[] = ['cartao-credito', 'pix', 'dinheiro', 'cartao-debito']
const status: PagamentoStatus[] = ['conciliado', 'pendente', 'divergente', 'conciliado']
const valoresCentavos = [35000, 18000, 25000, 42000, 12500, 98000, 6000, 27550]

/** Synthetic, repeatable data. Dates are relative to today so the prototype stays usable. */
export function criarPagamentosMock(unidadeId: number, referencia = new Date()): Pagamento[] {
  const hoje = dataCalendario(referencia)
  const datas: string[] = []

  // 24 payments today allow testing pagination with the default period.
  for (let index = 0; index < 60; index++) {
    const data = new Date(hoje)
    const diasAtras = index < 24 ? 0 : index < 36 ? 1 : 2 + (index % 5)
    data.setUTCDate(data.getUTCDate() - diasAtras)
    datas.push(data.toISOString().slice(0, 10))
  }

  // Include both months, even on the first day of a new month or year.
  for (const mesOffset of [0, -1]) {
    for (let index = 0; index < 12; index++) {
      const data = new Date(hoje)
      data.setUTCMonth(data.getUTCMonth() + mesOffset, 1 + index)
      if (data > hoje) continue
      datas.push(data.toISOString().slice(0, 10))
    }
  }

  return datas.map((data, index) => {
    const pacienteIndex = index % nomes.length
    return {
      id: `mock-pagamento-${unidadeId}-${index + 1}`,
      unidadeId,
      data,
      paciente: {
        id: unidadeId * 1000 + pacienteIndex + 1,
        nome: nomes[pacienteIndex]!,
        cpf: `000000${String(pacienteIndex + 1).padStart(3, '0')}00`
      },
      atendimento: {
        id: `ATD-${unidadeId}-${String(index + 1).padStart(4, '0')}`,
        descricao: atendimentos[index % atendimentos.length]!
      },
      formaPagamento: formas[index % formas.length]!,
      valorBrutoCentavos: valoresCentavos[index % valoresCentavos.length]! + (unidadeId % 5) * 500,
      status: status[index % status.length]!
    }
  })
}
