import type { H3Event } from 'h3'
import { createError, readBody } from 'h3'
import type { ZodType } from 'zod'

export async function readBodyWithSchema<T>(event: H3Event, schema: ZodType<T>, statusMessage = 'Dados inválidos') {
  const result = schema.safeParse(await readBody(event))
  if (!result.success) {
    throw createError({ statusCode: 400, statusMessage })
  }

  return result.data
}
