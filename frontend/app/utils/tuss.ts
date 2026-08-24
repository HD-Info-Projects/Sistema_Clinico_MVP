import type { TipoProcedimentoTuss } from '~/types'

type TipoProcedimentoColor = 'primary' | 'info' | 'error' | 'success' | 'secondary' | 'warning' | 'neutral' | 'quaternary' | 'tertiary' | 'quinary'

export const TUSS_PROCEDIMENTO_TIPOS: Array<{ value: TipoProcedimentoTuss, label: string, color: TipoProcedimentoColor }> = [
  { value: 'consulta', label: 'Consultas', color: 'primary' },
  { value: 'procedimento-ambulatorial', label: 'Procedimentos ambulatoriais', color: 'info' },
  { value: 'cirurgia', label: 'Cirurgias', color: 'error' },
  { value: 'metodos-eletrofisiologicos', label: 'Métodos Eletrofisiológicos/Mecânicos e Funcionais', color: 'secondary' },
  { value: 'endoscopia', label: 'Endoscopia', color: 'quaternary' },
  { value: 'medicina-laboratorial', label: 'Medicina Laboratorial', color: 'success' },
  { value: 'medicina-transfusional', label: 'Medicina Transfusional', color: 'error' },
  { value: 'genetica', label: 'Genética', color: 'tertiary' },
  { value: 'anatomia-patologica-citopatologia', label: 'Anatomia Patológica e Citopatologia', color: 'quinary' },
  { value: 'medicina-nuclear', label: 'Medicina Nuclear', color: 'secondary' },
  { value: 'radiologia-rx', label: 'Radiologia / RX', color: 'info' },
  { value: 'ultrassonografia-us', label: 'Ultrassonografia (US)', color: 'warning' },
  { value: 'tomografia-computadorizada', label: 'Tomografia Computadorizada (TC)', color: 'neutral' },
  { value: 'ressonancia-magnetica', label: 'Ressonância Magnética (RM)', color: 'quaternary' },
  { value: 'radioterapia', label: 'Radioterapia', color: 'error' },
  { value: 'exames-procedimentos-especificos', label: 'Exames/Procedimentos Específicos', color: 'primary' },
  { value: 'testes-diagnostico', label: 'Testes para Diagnóstico', color: 'success' },
  { value: 'outros-diagnosticos-terapeuticos', label: 'Outros Procedimentos Diagnósticos/Terapêuticos', color: 'tertiary' },
  { value: 'outros', label: 'Outros', color: 'tertiary' },
  { value: 'nao-informado', label: 'Não informado', color: 'neutral' }
]

export const TUSS_PROCEDIMENTO_FILTROS: Array<{ label: string, value: TipoProcedimentoTuss | '' }> = [
  { label: 'Todos os tipos', value: '' },
  ...TUSS_PROCEDIMENTO_TIPOS.map(tipo => ({ label: tipo.label, value: tipo.value }))
]

export function corTipoProcedimento(tipo: string | null | undefined) {
  return TUSS_PROCEDIMENTO_TIPOS.find(item => item.value === tipo)?.color ?? 'neutral'
}

export function rotuloTipoProcedimento(tipo: string | null | undefined, label?: string | null) {
  const texto = String(label ?? '').trim()
  if (texto) return texto

  return TUSS_PROCEDIMENTO_TIPOS.find(item => item.value === tipo)?.label ?? 'Não informado'
}
