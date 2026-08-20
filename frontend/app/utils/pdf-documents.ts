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

const LINHAS_BLOCO_RECEITA_DUPLA = 18

function montarBlocoTextoLinhas(params: {
  texto?: string
  medicamentos: ItemMedicamento[]
}) {
  const linhas = params.texto
    ? params.texto.split('\n')
    : params.medicamentos.map(m => `\u2022 ${m.nome}${m.dosagem ? ` — ${m.dosagem}` : ''}${m.detalhes ? `  ${m.detalhes}` : ''}`)

  const total = Math.max(linhas.length, LINHAS_BLOCO_RECEITA_DUPLA)

  return Array.from({ length: total }, (_v, i) => ({
    text: linhas[i] ? linhas[i] : '\u00A0',
    fontSize: 9,
    lineHeight: 1.3
  }))
}

async function montarCorpoReceitaEspecialDupla(params: {
  paciente: string
  data: string
  medicamentos: ItemMedicamento[]
  texto?: string
  medico?: string
  crm?: string
  especialidade?: string
}) {
  const logo = await getLogoBase64()

  const blocoMedicamentos = {
    stack: montarBlocoTextoLinhas(params),
    margin: [0, 0, 0, 8]
  }

  return [
    {
      columns: [
        { image: logo, width: 74, alignment: 'left' },
        {
          stack: [
            { text: 'HOSPITAL NATUS LUMINE', fontSize: 9, bold: true, alignment: 'right' },
            { text: 'Av. dos Holandeses, n\u00BA 69, Olho D\'Água', fontSize: 6.5, color: '#555555', alignment: 'right' },
            { text: 'São Luís - MA | CEP: 65065-180 | Tel: (98) 2107-5252', fontSize: 6.5, color: '#555555', alignment: 'right' }
          ],
          margin: [0, 2, 0, 0]
        }
      ],
      margin: [0, 0, 0, 6]
    },
    { canvas: [{ type: 'line', x1: 0, y1: 0, x2: 360, y2: 0, lineWidth: 0.5, lineColor: '#CCCCCC' }], margin: [0, 4, 0, 6] },
    { text: `DATA: ${params.data}`, fontSize: 9, alignment: 'right', margin: [0, 0, 0, 4] },
    { text: 'RECEITA DE CONTROLE ESPECIAL', fontSize: 13, bold: true, alignment: 'center', margin: [0, 2, 0, 10] },
    { text: `PACIENTE: ${params.paciente.toUpperCase()}`, bold: true, fontSize: 9, decoration: 'underline', margin: [0, 0, 0, 8] },
    blocoMedicamentos,
    {
      stack: [
        { text: '\n\n' },
        { text: '________________________________________________', alignment: 'center', fontSize: 9, margin: [0, 4, 0, 2] },
        { text: params.medico ?? 'Médico Responsável', bold: true, fontSize: 8, alignment: 'center' },
        ...(params.especialidade ? [{ text: params.especialidade, fontSize: 7, alignment: 'center', color: '#555555' }] : []),
        ...(params.crm ? [{ text: `CRM:${params.crm}`, fontSize: 7, alignment: 'center', color: '#555555' }] : [])
      ],
      unbreakable: true,
      margin: [0, 0, 0, 8]
    },
    {
      table: {
        widths: ['50%', '50%'],
        body: [[
          {
            stack: [
              { text: 'IDENTIFICAÇÃO DO COMPRADOR', bold: true, fontSize: 7, alignment: 'center', margin: [0, 0, 0, 4] },
              { text: 'Nome: ________________________________', fontSize: 6.5, margin: [0, 0, 0, 2] },
              { text: 'Identidade: ______________________', fontSize: 6.5, margin: [0, 0, 0, 2] },
              { text: 'Org. Emissor: ____________________', fontSize: 6.5, margin: [0, 0, 0, 2] },
              { text: 'Endereço: ________________________________', fontSize: 6.5, margin: [0, 0, 0, 2] },
              { text: 'Cidade: ________________  UF: ____', fontSize: 6.5, margin: [0, 0, 0, 2] },
              { text: 'Telefone: __________________________', fontSize: 6.5, margin: [0, 0, 0, 2] }
            ],
            border: [true, true, true, true],
            padding: 5
          },
          {
            stack: [
              { text: 'IDENTIFICAÇÃO DO FORNECEDOR', bold: true, fontSize: 7, alignment: 'center', margin: [0, 0, 0, 4] },
              { text: '\n' },
              { text: 'Assinatura do Farmacêutico:', fontSize: 6.5, alignment: 'center', margin: [0, 0, 0, 6] },
              { text: '____________________________________', fontSize: 6.5, alignment: 'center', margin: [0, 0, 0, 10] },
              { text: 'Data: ______ / ______ / ______', fontSize: 6.5, alignment: 'center' }
            ],
            border: [true, true, true, true],
            padding: 5
          }
        ]]
      }
    }
  ]
}

export async function buildReceitaEspecialDupla(params: {
  paciente: string
  data: string
  medicamentos: ItemMedicamento[]
  texto?: string
  medico?: string
  crm?: string
  especialidade?: string
}) {
  const esquerda = montarCorpoReceitaEspecialDupla(params)
  const direita = montarCorpoReceitaEspecialDupla(params)
  const [esq, dir] = await Promise.all([esquerda, direita])

  return {
    pageSize: 'A4',
    pageOrientation: 'landscape',
    pageMargins: [10, 10, 10, 10],
    content: [
      {
        table: {
          widths: ['*', 12, '*'],
          body: [[
            { stack: esq, border: [true, true, true, true], padding: 8 },
            { text: '', border: [false, false, false, false] },
            { stack: dir, border: [true, true, true, true], padding: 8 }
          ]]
        }
      }
    ],
    defaultStyle: { fontSize: 9, lineHeight: 1.3 }
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

export async function buildSolicitacaoOpme(params: {
  paciente: string
  data: string
  opmeItens?: { codigo?: string, nome: string, quantidade?: number }[]
  indicacaoClinica?: string
  medico?: string
  crm?: string
  especialidade?: string
}) {
  const linhasOpme = (params.opmeItens ?? []).map((opme) => {
    const codigo = opme.codigo ? `${opme.codigo} - ` : ''
    const qtd = opme.quantidade && opme.quantidade > 1 ? `  (x${opme.quantidade})` : ''
    return `\u2022 ${codigo}${opme.nome}${qtd}`
  })

  return {
    pageSize: 'A4' as const,
    pageMargins: [60, 40, 60, 60] as [number, number, number, number],
    content: [
      ...(await hospitalHeader()),
      documentTitle('SOLICITA\u00C7\u00C3O DE OPME'),
      { text: `PACIENTE: ${params.paciente.toUpperCase()}`, bold: true, decoration: 'underline', margin: [0, 0, 0, 5] },
      { text: `DATA: ${params.data}`, margin: [0, 0, 0, 20] },
      ...(params.indicacaoClinica?.trim()
        ? [
            { text: 'INDICA\u00C7\u00C3O CL\u00CDNICA:', bold: true, margin: [0, 0, 0, 5] },
            { text: params.indicacaoClinica.trim(), margin: [0, 0, 0, 20] }
          ]
        : []),
      ...linhasOpme.map(opme => ({ text: `\u2022 ${opme}`, margin: [0, 0, 0, 4] })),
      signatureBlock(params.medico, params.crm, params.especialidade)
    ],
    defaultStyle
  }
}
