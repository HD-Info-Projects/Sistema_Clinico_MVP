import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { createServer } from 'node:http'
import { once } from 'node:events'
import { test } from 'node:test'
import { runInNewContext } from 'node:vm'
import { createRequire } from 'node:module'
import ts from 'typescript'

// h3 is supplied by Nuxt; resolve it through Nuxt under pnpm's isolated layout.
const requireFromNuxt = createRequire(import.meta.resolve('nuxt/package.json'))
const h3 = await import(requireFromNuxt.resolve('h3'))

const source = readFileSync(new URL('../server/middleware/root-auth.ts', import.meta.url), 'utf8')
const { outputText } = ts.transpileModule(source, {
  compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022 }
})
const exports = {}
runInNewContext(outputText, {
  exports,
  require(name) {
    if (name === 'h3') return h3
    if (name === '../utils/auth') return { AUTH_COOKIE_NAME: 'auth_token' }
    throw new Error(`Unexpected import: ${name}`)
  }
})

test('entry redirect is resolved before rendering, based on the session cookie', async (t) => {
  const app = h3.createApp()
  app.use(exports.default)
  app.use(h3.defineEventHandler(() => 'rendered page'))
  const server = createServer(h3.toNodeListener(app))
  server.listen(0, '127.0.0.1')
  await once(server, 'listening')
  t.after(() => new Promise((resolve, reject) => {
    server.close(error => error ? reject(error) : resolve())
    server.closeAllConnections()
  }))
  const baseURL = `http://127.0.0.1:${server.address().port}`

  for (const path of ['/', '/?origem=link']) {
    const response = await fetch(`${baseURL}${path}`, { redirect: 'manual' })
    assert.equal(response.status, 302)
    assert.equal(response.headers.get('location'), '/login')
    assert.equal(response.headers.get('cache-control'), 'private, no-store')
    assert.notEqual(await response.text(), 'rendered page')
  }

  const unrelatedCookie = await fetch(`${baseURL}/`, {
    redirect: 'manual',
    headers: { Cookie: 'access_mode=financeiro' }
  })
  assert.equal(unrelatedCookie.status, 302)

  const withSession = await fetch(`${baseURL}/`, {
    redirect: 'manual',
    headers: { Cookie: 'auth_token=session-to-be-validated' }
  })
  assert.equal(withSession.status, 200)
  assert.equal(withSession.headers.get('location'), null)
  assert.equal(withSession.headers.get('cache-control'), 'private, no-store')
  assert.equal(await withSession.text(), 'rendered page')

  for (const path of ['/login', '/api/auth/me', '/financeiro/pagamentos', '/painel-chamada/1']) {
    const response = await fetch(`${baseURL}${path}`, { redirect: 'manual' })
    assert.equal(response.status, 200)
    assert.equal(response.headers.get('location'), null)
    assert.equal(await response.text(), 'rendered page')
  }
})
