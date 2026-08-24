/* eslint-disable @typescript-eslint/no-explicit-any */
import type { PadraoAnamnese } from '~/types'

export default defineEventHandler(async (event): Promise<PadraoAnamnese> => {
  const id = getRouterParam(event, 'id')
  if (!id) {
    throw createError({ statusCode: 400, statusMessage: 'id é obrigatório' })
  }

  const body = await readBody(event)

  const raw = await flaskFetch<any>(event, `/padrao_medico_anamnese/editar/${id}`, {
    params: medicoAlvoParams(event),
    method: 'PUT',
    body: { nome_modelo: body.nome, conteudo: body.conteudo }
  })

  return {
    id: String(raw.id),
    medicoId: Number(raw.medico_id) || 0,
    nome: raw.nome_modelo,
    conteudo: raw.conteudo || '',
    createdAt: raw.created_at,
    updatedAt: raw.updated_at
  }
})
