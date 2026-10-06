import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { test } from 'node:test'
import { runInNewContext } from 'node:vm'
import ts from 'typescript'

const source = readFileSync(new URL('../app/middleware/00.layout.global.ts', import.meta.url), 'utf8')
const { outputText } = ts.transpileModule(source, {
  compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022 }
})
const exports = {}
runInNewContext(outputText, { exports, defineNuxtRouteMiddleware: handler => handler })
const selectLayout = exports.default

for (const [path, expected] of [
  ['/login', 'auth'],
  ['/selecionar-clinica', 'auth'],
  ['/selecionar-acesso', 'auth'],
  ['/painel-chamada', 'tv'],
  ['/painel-chamada/7', 'tv'],
  ['/atendimento-medico', 'atendimento'],
  ['/recepcao/novo-atendimento', 'recepcao'],
  ['/admin/medicos', 'admin'],
  ['/dashboard', 'default'],
  ['/agenda', 'default'],
  ['/acesso-negado', false]
]) {
  test(`selects ${expected} for ${path} before page rendering`, () => {
    const to = { path, meta: {} }
    selectLayout(to)
    assert.equal(to.meta.layout, expected)
  })
}

test('hydration redirect selects destination layout without waiting for the previous page slot', () => {
  const initial = { path: '/atendimento-medico', meta: {} }
  selectLayout(initial)
  const dashboard = { path: '/dashboard', meta: {} }
  selectLayout(dashboard)
  assert.equal(initial.meta.layout, 'atendimento')
  assert.equal(dashboard.meta.layout, 'default')
})

test('explicit page layout and disabled layouts are preserved', () => {
  const to = { path: '/admin/example', meta: { layout: false } }
  selectLayout(to)
  assert.equal(to.meta.layout, false)
  to.meta.layout = 'auth'
  selectLayout(to)
  assert.equal(to.meta.layout, 'auth')
})
