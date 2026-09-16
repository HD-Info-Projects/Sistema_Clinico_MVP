export type {
  Padrao,
  PadraoAnamnese,
  PadraoExame,
  PadraoOrientacaoExame,
  PadraoReceita
} from '~/types'

export type PadraoPayload = {
  nome: string
  tipo: string
  [key: string]: unknown
}

export type PadraoTextoPayload = {
  nome: string
  conteudo: string
}

export type CidResultado = { cid: string, nome: string }
