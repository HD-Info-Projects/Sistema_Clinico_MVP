export function formatarCpfCnpj(valor: string): string {
  const digitos = (valor ?? '').replace(/\D/g, '').slice(0, 14)

  if (digitos.length <= 11) {
    let resultado = digitos.slice(0, 3)
    if (digitos.length > 3) resultado += `.${digitos.slice(3, 6)}`
    if (digitos.length > 6) resultado += `.${digitos.slice(6, 9)}`
    if (digitos.length > 9) resultado += `-${digitos.slice(9, 11)}`
    return resultado
  }

  let resultado = digitos.slice(0, 2)
  if (digitos.length > 2) resultado += `.${digitos.slice(2, 5)}`
  if (digitos.length > 5) resultado += `.${digitos.slice(5, 8)}`
  if (digitos.length > 8) resultado += `/${digitos.slice(8, 12)}`
  if (digitos.length > 12) resultado += `-${digitos.slice(12, 14)}`
  return resultado
}

export function formatarTelefone(valor: string): string {
  const digitos = (valor ?? '').replace(/\D/g, '').slice(0, 11)

  if (digitos.length === 0) return ''

  let resultado = `(${digitos.slice(0, 2)}`

  if (digitos.length > 2) {
    resultado += ') '
    if (digitos.length <= 10) {
      resultado += digitos.slice(2, 6)
      if (digitos.length > 6) resultado += `-${digitos.slice(6, 10)}`
    } else {
      resultado += `${digitos.slice(2, 7)}-${digitos.slice(7, 11)}`
    }
  }

  return resultado
}
