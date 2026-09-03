import type { TipoProcedimentoTuss } from '~/types'

type TipoProcedimentoColor = 'primary' | 'info' | 'error' | 'success' | 'secondary' | 'warning' | 'neutral' | 'quaternary' | 'tertiary' | 'quinary'

export const TUSS_PROCEDIMENTO_TIPOS: Array<{ value: TipoProcedimentoTuss, label: string, color: TipoProcedimentoColor }> = [
  { value: 'consulta', label: 'Consultas', color: 'primary' },
  { value: 'procedimento-ambulatorial', label: 'Procedimentos', color: 'info' },
  { value: 'cirurgia', label: 'Cirurgias', color: 'error' },
  { value: 'metodos-eletrofisiologicos', label: 'Métodos Funcionais', color: 'secondary' },
  { value: 'endoscopia', label: 'Endoscopia', color: 'quaternary' },
  { value: 'medicina-laboratorial', label: 'Laboratório', color: 'success' },
  { value: 'medicina-transfusional', label: 'Hemoterapia', color: 'error' },
  { value: 'genetica', label: 'Genética', color: 'tertiary' },
  { value: 'anatomia-patologica-citopatologia', label: 'Anatomia Patológica', color: 'quinary' },
  { value: 'medicina-nuclear', label: 'Medicina Nuclear', color: 'secondary' },
  { value: 'radiologia-rx', label: 'Radiologia', color: 'info' },
  { value: 'ultrassonografia-us', label: 'Ultrassonografia', color: 'warning' },
  { value: 'tomografia-computadorizada', label: 'Tomografia', color: 'neutral' },
  { value: 'ressonancia-magnetica', label: 'Ressonância', color: 'quaternary' },
  { value: 'radioterapia', label: 'Radioterapia', color: 'error' },
  { value: 'exames-procedimentos-especificos', label: 'Exames Específicos', color: 'primary' },
  { value: 'testes-diagnostico', label: 'Testes Diagnósticos', color: 'success' },
  { value: 'outros-diagnosticos-terapeuticos', label: 'Outros Diagnósticos', color: 'tertiary' },
  { value: 'outros', label: 'Outros', color: 'tertiary' },
  { value: 'nao-informado', label: 'Não informado', color: 'neutral' }
]

export const TUSS_PROCEDIMENTO_FILTROS: Array<{ label: string, value: TipoProcedimentoTuss }> = [
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
