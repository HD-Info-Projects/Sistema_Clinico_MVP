import type { ItemMedicamento } from '~/types'
import { getLogoBase64 } from '~/utils/pdf-assets'

type ExameSolicitacaoPdf = string | {
  nome: string
  orientacao?: string | null
}

type ProcedimentoSolicitacaoPdf = string | {
  nome: string
  codigo_procedimento?: string | number | null
  tipo_ato_nome?: string | null
}

async function hospitalHeader() {
  const logo = await getLogoBase64()
  return [
    {
      columns: [
        {
          image: logo,
          width: 160
        },
        {
          stack: [
            { text: 'NATUS LUMINE HOSPITAL E MATERNIDADE', fontSize: 12, bold: true },
            { text: 'Av. dos Holandeses, n\u00BA 69, Olho D\'Água', fontSize: 9, color: '#555555' },
            { text: 'São Luís - MA | CEP: 65065-180', fontSize: 9, color: '#555555' },
            { text: 'Telefone: (98) 2107-5252', fontSize: 9, color: '#555555' }
          ],
          alignment: 'right' as const,
          margin: [0, 5, 0, 0]
        }
      ]
    },
    { text: '\n' },
    { canvas: [{ type: 'line', x1: 0, y1: 0, x2: 475, y2: 0, lineWidth: 1, lineColor: '#E0E0E0' }] },
    { text: '\n' }
  ]
}

function documentTitle(title: string) {
  return { text: title, fontSize: 16, bold: true, alignment: 'center' as const, margin: [0, 10, 0, 20] }
}

function signatureBlock(medico?: string, crm?: string, especialidade?: string) {
  return {
    stack: [
      { text: '\n\n\n' },
      { text: '__________________________________________', alignment: 'center' as const },
      { text: medico ?? 'Médico Responsável', bold: true, fontSize: 10, alignment: 'center' as const },
      ...(especialidade ? [{ text: especialidade, fontSize: 9, alignment: 'center' as const, color: '#555555' }] : []),
      ...(crm ? [{ text: `CRM:${crm}`, fontSize: 9, alignment: 'center' as const, color: '#555555' }] : [])
    ],
    unbreakable: true
  }
}

const defaultStyle = { fontSize: 11, lineHeight: 1.5 }

function htmlTemConteudo(valor?: string | null) {
  const texto = (valor || '')
    .replace(/<[^>]*>/g, ' ')
    .replace(/&nbsp;|&#160;|&#xA0;/gi, ' ')
    .replace(/[\u00A0\u200B-\u200D\uFEFF]/g, '')
    .trim()

  return Boolean(texto)
}

function normalizarExameSolicitacao(exame: ExameSolicitacaoPdf) {
  if (typeof exame === 'string') {
    return { nome: exame, orientacao: null }
  }

  return {
    nome: exame.nome,
    orientacao: htmlTemConteudo(exame.orientacao) ? exame.orientacao || null : null
  }
}

function normalizarProcedimentoSolicitacao(procedimento: ProcedimentoSolicitacaoPdf) {
  if (typeof procedimento === 'string') {
    return { nome: procedimento, codigo_procedimento: null, tipo_ato_nome: null }
  }

  return {
    nome: procedimento.nome,
    codigo_procedimento: procedimento.codigo_procedimento ?? null,
    tipo_ato_nome: procedimento.tipo_ato_nome ?? null
  }
}

export async function buildSolicitacaoExames(params: {
  paciente: string
  data: string
  exames: ExameSolicitacaoPdf[]
  medico?: string
  crm?: string
  especialidade?: string
}) {
  const htmlToPdfmake = (await import('html-to-pdfmake')).default
  const exames = params.exames.map(normalizarExameSolicitacao)
  const folhasOrientacao = exames.filter(e => htmlTemConteudo(e.orientacao))

  return {
    pageSize: 'A4' as const,
    pageMargins: [60, 40, 60, 60] as [number, number, number, number],
    content: [
      ...(await hospitalHeader()),
      documentTitle('SOLICITAÇÃO DE EXAMES'),
      { text: `PACIENTE: ${params.paciente.toUpperCase()}`, bold: true, decoration: 'underline', margin: [0, 0, 0, 5] },
      { text: `DATA: ${params.data}`, margin: [0, 0, 0, 20] },
      ...exames.map(e => ({ text: `\u2022 ${e.nome}`, margin: [0, 0, 0, 4] })),
      signatureBlock(params.medico, params.crm, params.especialidade),
      ...(
        await Promise.all(folhasOrientacao.map(async e => [
          { text: '', pageBreak: 'before' as const },
          ...(await hospitalHeader()),
          documentTitle('ORIENTAÇÃO DE EXAME'),
          { text: `PACIENTE: ${params.paciente.toUpperCase()}`, bold: true, decoration: 'underline', margin: [0, 0, 0, 5] },
          { text: `DATA: ${params.data}`, margin: [0, 0, 0, 5] },
          { text: `EXAME: ${e.nome}`, bold: true, margin: [0, 0, 0, 20] },
          ...htmlToPdfmake(e.orientacao || '', { window }),
          signatureBlock(params.medico, params.crm, params.especialidade)
        ]))
      ).flat()
    ],
    defaultStyle
  }
}

export async function buildReceita(params: {
  paciente: string
  data: string
  medicamentos: ItemMedicamento[]
  texto?: string
  medico?: string
  crm?: string
  especialidade?: string
}) {
  const medicamentosContent = params.texto
    ? [{ text: params.texto, margin: [0, 0, 0, 20] }]
    : params.medicamentos.map(m => ({
        columns: [
          { text: `\u2022 ${m.nome} — ${m.dosagem}`, bold: true, width: '40%' as const },
          { text: m.detalhes, width: '60%' as const }
        ],
        margin: [0, 0, 0, 12] as [number, number, number, number]
      }))

  return {
    pageSize: 'A4' as const,
    pageMargins: [60, 40, 60, 60] as [number, number, number, number],
    content: [
      ...(await hospitalHeader()),
      { text: `DATA: ${params.data}`, margin: [0, 0, 0, 0], alignment: 'right' as const },
      documentTitle('RECEITA MÉDICA'),
      { text: `PACIENTE: ${params.paciente.toUpperCase()}`, bold: true, decoration: 'underline', margin: [0, 0, 0, 5] },
      ...medicamentosContent,
      signatureBlock(params.medico, params.crm, params.especialidade)
    ],
    defaultStyle
  }
}

export async function buildReceitaEspecial(params: {
  paciente: string
  data: string
  medicamentos: ItemMedicamento[]
  texto?: string
  medico?: string
  crm?: string
  especialidade?: string
}) {
  const medicamentosContent = params.texto
    ? [{ text: params.texto, margin: [0, 0, 0, 10] }]
    : params.medicamentos.map(m => ({
        columns: [
          { text: `\u2022 ${m.nome} — ${m.dosagem}`, bold: true, width: '40%' as const },
          { text: m.detalhes, width: '60%' as const }
        ],
        margin: [0, 0, 0, 12] as [number, number, number, number]
      }))

  return {
    pageSize: 'A4',
    pageMargins: [60, 40, 60, 340],
    content: [
      ...(await hospitalHeader()),
      { text: `DATA: ${params.data}`, margin: [0, 0, 0, 0], alignment: 'right' },
      documentTitle('RECEITA DE CONTROLE ESPECIAL'),
      { text: `PACIENTE: ${params.paciente.toUpperCase()}`, bold: true, decoration: 'underline', margin: [0, 0, 0, 5] },
      ...medicamentosContent
    ],
    footer: function (_currentPage: number, _pageCount: number) {
      return {
        margin: [60, 0, 60, 0],
        stack: [
          signatureBlock(params.medico, params.crm, params.especialidade),
          { text: '\n' },
          {
            table: {
              widths: ['50%', '50%'],
              body: [[
                {
                  stack: [
                    { text: 'IDENTIFICAÇÃO DO COMPRADOR', bold: true, fontSize: 9, alignment: 'center', margin: [0, 0, 0, 6] },
                    { text: 'Nome: _______________________________________________', fontSize: 8, margin: [0, 0, 0, 3] },
                    { text: 'Identidade: _____________________________', fontSize: 8, margin: [0, 0, 0, 3] },
                    { text: 'Org. Emissor: ___________________________', fontSize: 8, margin: [0, 0, 0, 3] },
                    { text: 'Endereço: ______________________________________________', fontSize: 8, margin: [0, 0, 0, 3] },
                    { text: 'Cidade: _________________________________', fontSize: 8, margin: [0, 0, 0, 3] },
                    { text: 'UF: ______________________', fontSize: 8, margin: [0, 0, 0, 3] },
                    { text: 'Telefone: _______________________________', fontSize: 8, margin: [0, 0, 0, 3] }
                  ],
                  border: [true, true, true, true]
                },
                {
                  stack: [
                    { text: 'IDENTIFICAÇÃO DO FORNECEDOR', bold: true, fontSize: 9, alignment: 'center', margin: [0, 0, 0, 6] },
                    { text: '\n\n\n' },
                    { text: 'Assinatura do Farmacêutico:', fontSize: 8, alignment: 'center', margin: [0, 0, 0, 2] },
                    { text: '____________________________________________', fontSize: 8, alignment: 'center', margin: [0, 0, 0, 14] },
                    { text: 'Data: ________ / ________ / ________', fontSize: 8, alignment: 'center', margin: [0, 0, 0, 3] }
                  ],
                  border: [true, true, true, true]
                }
              ]]
            },
            margin: [0, 0, 0, 0]
          }
        ]
      }
    },
    defaultStyle
  }
}

export async function buildAtestadoComparecimento(params: {
  paciente: string
  data: string
  horario: string
  medico?: string
  crm?: string
  especialidade?: string
}) {
  return {
    pageSize: 'A4' as const,
    pageMargins: [60, 40, 60, 60] as [number, number, number, number],
    content: [
      ...(await hospitalHeader()),
      documentTitle('ATESTADO DE COMPARECIMENTO'),
      { text: `PACIENTE: ${params.paciente.toUpperCase()}`, bold: true, decoration: 'underline', margin: [0, 0, 0, 5] },
      { text: '\n' },
      { text: `Atesto, para os devidos fins, que o(a) paciente ${params.paciente} compareceu a esta unidade de sa\u00FAdde no dia ${params.data} \u00E0s ${params.horario}, para atendimento m\u00E9dico.`, margin: [0, 0, 0, 10] },
      signatureBlock(params.medico, params.crm, params.especialidade)
    ],
    defaultStyle
  }
}

export async function buildAtestado(params: {
  paciente: string
  conteudoHtml: string
  medico?: string
  crm?: string
  especialidade?: string
}) {
  const htmlToPdfmake = (await import('html-to-pdfmake')).default

  return {
    pageSize: 'A4' as const,
    pageMargins: [60, 40, 60, 60] as [number, number, number, number],
    content: [
      ...(await hospitalHeader()),
      documentTitle('ATESTADO MÉDICO'),
      ...htmlToPdfmake(params.conteudoHtml, { window }),
      signatureBlock(params.medico, params.crm, params.especialidade)
    ],
    defaultStyle
  }
}

export async function buildEncaminhamento(params: {
  paciente: string
  data: string
  encaminharPara: string
  profissionalExterno: string
  medico?: string
  crm?: string
  especialidade?: string
}) {
  const profissional = params.profissionalExterno.trim() || 'n\u00E3o informado'

  return {
    pageSize: 'A4' as const,
    pageMargins: [60, 40, 60, 60] as [number, number, number, number],
    content: [
      ...(await hospitalHeader()),
      documentTitle('ENCAMINHAMENTO M\u00C9DICO'),
      { text: `PACIENTE: ${params.paciente.toUpperCase()}`, bold: true, decoration: 'underline', margin: [0, 0, 0, 5] },
      { text: `DATA: ${params.data}`, margin: [0, 0, 0, 20] },
      { text: `Encaminho para ${params.encaminharPara}`, margin: [0, 0, 0, 10] },
      { text: `Profissional Externo: ${profissional}`, margin: [0, 0, 0, 10] },
      signatureBlock(params.medico, params.crm, params.especialidade)
    ],
    defaultStyle
  }
}

export async function buildSolicitacaoProcedimento(params: {
  paciente: string
  data: string
  descricao: string
  procedimentos?: ProcedimentoSolicitacaoPdf[]
  medico?: string
  crm?: string
  especialidade?: string
}) {
  const htmlToPdfmake = (await import('html-to-pdfmake')).default
  const procedimentos = (params.procedimentos || [])
    .map(normalizarProcedimentoSolicitacao)
    .filter(p => p.nome?.trim())
  const conteudoProcedimentos = procedimentos.length
    ? procedimentos.flatMap((p) => {
        const codigo = p.codigo_procedimento ? `${p.codigo_procedimento} - ` : ''
        return [
          { text: `• ${codigo}${p.nome}`, margin: [0, 0, 0, p.tipo_ato_nome ? 0 : 4] },
          ...(p.tipo_ato_nome
            ? [{ text: `Tipo: ${p.tipo_ato_nome}`, fontSize: 9, color: '#555555', margin: [14, 0, 0, 4] }]
            : [])
        ]
      })
    : htmlToPdfmake(`<p>${params.descricao}</p>`, { window })

  return {
    pageSize: 'A4' as const,
    pageMargins: [60, 40, 60, 60] as [number, number, number, number],
    content: [
      ...(await hospitalHeader()),
      documentTitle('SOLICITA\u00C7\u00C3O DE PROCEDIMENTO'),
      { text: `PACIENTE: ${params.paciente.toUpperCase()}`, bold: true, decoration: 'underline', margin: [0, 0, 0, 5] },
      { text: `DATA: ${params.data}`, margin: [0, 0, 0, 20] },
      ...conteudoProcedimentos,
      signatureBlock(params.medico, params.crm, params.especialidade)
    ],
    defaultStyle
  }
}
