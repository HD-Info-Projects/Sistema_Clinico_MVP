import type { TipoProcedimentoTuss } from '~/types'

type TipoProcedimentoColor = 'primary' | 'info' | 'error' | 'success' | 'secondary' | 'warning' | 'neutral' | 'quaternary' | 'tertiary' | 'quinary'
type TipoProcedimentoFaixa = readonly [inicio: number, fim: number, tipo: TipoProcedimentoTuss]

export const TUSS_PROCEDIMENTO_TIPOS: Array<{ value: TipoProcedimentoTuss, label: string, color: TipoProcedimentoColor }> = [
  { value: 'consulta', label: 'Consultas', color: 'primary' },
  { value: 'procedimento-ambulatorial', label: 'Procedimentos ambulatoriais', color: 'info' },
  { value: 'cirurgia', label: 'Cirurgias', color: 'error' },
  { value: 'anatomia-patologica', label: '8 - Anatomia Patológica', color: 'quinary' },
  { value: 'alergologia', label: '9 - Alergologia', color: 'warning' },
  { value: 'eletroencefalografia', label: '10 - Eletroencefalografia', color: 'secondary' },
  { value: 'fisioterapia', label: '11 - Fisioterapia', color: 'success' },
  { value: 'hemoterapia', label: '12 - Hemoterapia', color: 'error' },
  { value: 'endoscopia-peroral', label: '13 - Endoscopia Peroral', color: 'quaternary' },
  { value: 'medicina-nuclear', label: '14 - Medicina Nuclear', color: 'secondary' },
  { value: 'patologia-clinica', label: '15 - Patologia Clínica', color: 'success' },
  { value: 'radiodiagnostico', label: '16 - Radiodiagnóstico', color: 'info' },
  { value: 'radioterapia', label: '17 - Radioterapia', color: 'error' },
  { value: 'cardiologia', label: '18 - Cardiologia', color: 'primary' },
  { value: 'genetica', label: '20 - Genética', color: 'tertiary' },
  { value: 'endoscopia-digestiva', label: '21 - Endoscopia Digestiva', color: 'quaternary' },
  { value: 'tisiopneumologia', label: '22 - Tisiopneumologia', color: 'neutral' },
  { value: 'quimioterapia-cancer', label: '23 - Quimioterapia do Câncer', color: 'error' },
  { value: 'ultrassonografia', label: '24 - Ultrassonografia', color: 'warning' },
  { value: 'tomografia-computadorizada', label: '25 - Tomografia Computadorizada', color: 'neutral' },
  { value: 'ressonancia-magnetica', label: '26 - Ressonância Magnética', color: 'quaternary' },
  { value: 'ecocardiograma-doppler', label: '27 - Ecocardiograma com Doppler', color: 'primary' },
  { value: 'fonoaudiologia', label: '28 - Fonoaudiologia', color: 'success' },
  { value: 'exames-especificos', label: '40 - Exames Específicos', color: 'primary' },
  { value: 'testes-diagnostico', label: '41 - Testes para Diagnóstico', color: 'success' },
  { value: 'outros-diagnosticos-terapeuticos', label: 'Outros Procedimentos Diagnósticos/Terapêuticos', color: 'tertiary' },
  { value: 'outros', label: 'Outros', color: 'tertiary' },
  { value: 'nao-informado', label: 'Não informado', color: 'neutral' }
]

export const TUSS_PROCEDIMENTO_FILTROS: Array<{ label: string, value: TipoProcedimentoTuss }> = [
  ...TUSS_PROCEDIMENTO_TIPOS.map(tipo => ({ label: tipo.label, value: tipo.value }))
]

const CODIGOS_TUSS_CONSULTA_EXATOS = new Set(['5001'])

function codigosParaTipo(codigos: readonly string[], tipo: TipoProcedimentoTuss) {
  return Object.fromEntries(codigos.map(codigo => [codigo, tipo])) as Record<string, TipoProcedimentoTuss>
}

const CODIGOS_TUSS_TIPOS_EXATOS: Record<string, TipoProcedimentoTuss> = {
  ...codigosParaTipo(['40307255', '40307263', '40307905'], 'alergologia'),
  ...codigosParaTipo(['40101061'], 'tisiopneumologia'),
  ...codigosParaTipo([
    '40201031', '40201058', '40201198', '40201201', '40201210', '40201228',
    '40201236', '40201244', '40201252', '40201260', '40201309', '40201325',
    '40202011', '40202054', '40202100', '40202127', '40202151', '40202160',
    '40202178', '40202364', '40202372', '40202399', '40202429', '40202437',
    '40202445', '40202488', '40202585', '40202593', '40202623', '40202631',
    '40202763'
  ], 'endoscopia-peroral'),
  ...codigosParaTipo(['40813908', '40813924'], 'quimioterapia-cancer'),
  ...codigosParaTipo([
    '40901050', '40901068', '40901076', '40901084', '40901092', '40901106',
    '40902072', '40902080'
  ], 'ecocardiograma-doppler'),
  ...codigosParaTipo([
    '40103013', '40103048', '40103064', '40103072', '40103080', '40103099',
    '40103102', '40103110', '40103153', '40103161', '40103269', '40103285',
    '40103404', '40103412', '40103420', '40103439', '40103455', '40103463',
    '40103480', '40103498', '40103501', '40103552', '40103579', '40103641',
    '40103650', '40103668', '40103676', '40103722', '40103749', '40103765'
  ], 'fonoaudiologia'),
  ...codigosParaTipo([
    '40103021', '40103030', '40103137', '40103242', '40103250', '40103447',
    '40103633'
  ], 'exames-especificos')
}

const FAIXAS_TUSS_ESPECIFICAS: TipoProcedimentoFaixa[] = [
  [40101000, 40101999, 'cardiologia'],
  [40102000, 40102999, 'endoscopia-digestiva'],
  [40103000, 40103999, 'eletroencefalografia'],
  [40104000, 40104999, 'fisioterapia'],
  [40105000, 40105999, 'tisiopneumologia'],
  [40810000, 40810999, 'cardiologia']
]

const FAIXAS_TUSS: TipoProcedimentoFaixa[] = [
  [10000000, 19999999, 'consulta'],
  [20000000, 29999999, 'procedimento-ambulatorial'],
  [30000000, 39999999, 'cirurgia'],
  [40100000, 40199999, 'eletroencefalografia'],
  [40200000, 40299999, 'endoscopia-digestiva'],
  [40300000, 40399999, 'patologia-clinica'],
  [40400000, 40499999, 'hemoterapia'],
  [40500000, 40599999, 'genetica'],
  [40600000, 40699999, 'anatomia-patologica'],
  [40700000, 40799999, 'medicina-nuclear'],
  [40800000, 40899999, 'radiodiagnostico'],
  [40900000, 40999999, 'ultrassonografia'],
  [41000000, 41099999, 'tomografia-computadorizada'],
  [41100000, 41199999, 'ressonancia-magnetica'],
  [41200000, 41299999, 'radioterapia'],
  [41300000, 41399999, 'exames-especificos'],
  [41400000, 41499999, 'testes-diagnostico'],
  [41500000, 41599999, 'outros-diagnosticos-terapeuticos']
]

export function normalizarCodigoTuss(valor: string | number | null | undefined) {
  const texto = String(valor ?? '').trim()
  if (!texto) return ''

  const codigo = Number(texto.replace(',', '.'))
  if (!Number.isFinite(codigo) || codigo <= 0) return ''

  return String(Math.trunc(codigo))
}

export function tipoProcedimentoPorCodigoTuss(codigo: string | number | null | undefined): TipoProcedimentoTuss {
  const codigoTexto = normalizarCodigoTuss(codigo)
  if (!codigoTexto) return 'nao-informado'

  if (CODIGOS_TUSS_CONSULTA_EXATOS.has(codigoTexto)) return 'consulta'

  const tipoExato = CODIGOS_TUSS_TIPOS_EXATOS[codigoTexto]
  if (tipoExato) return tipoExato

  const codigoNumero = Number(codigoTexto)
  for (const [inicio, fim, tipo] of FAIXAS_TUSS_ESPECIFICAS) {
    if (codigoNumero >= inicio && codigoNumero <= fim) return tipo
  }

  for (const [inicio, fim, tipo] of FAIXAS_TUSS) {
    if (codigoNumero >= inicio && codigoNumero <= fim) return tipo
  }

  return 'outros'
}

export function corTipoProcedimento(tipo: string | null | undefined) {
  return TUSS_PROCEDIMENTO_TIPOS.find(item => item.value === tipo)?.color ?? 'neutral'
}

export function rotuloTipoProcedimento(tipo: string | null | undefined, label?: string | null) {
  const texto = String(label ?? '').trim()
  if (texto) return texto

  return TUSS_PROCEDIMENTO_TIPOS.find(item => item.value === tipo)?.label ?? 'Não informado'
}
