import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { test } from 'node:test'
import { runInNewContext } from 'node:vm'
import ts from 'typescript'

function loadModule(path, globals = {}) {
  const source = readFileSync(new URL(path, import.meta.url), 'utf8')
    .replaceAll('import.meta.server', 'false')
    .replaceAll('import.meta.client', 'true')
  const { outputText } = ts.transpileModule(source, {
    compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022 }
  })
  const exports = {}
  runInNewContext(outputText, { exports, ...globals })
  return exports
}

const roles = loadModule('../app/utils/roles.ts')
const authExports = loadModule('../app/stores/auth.ts', {
  require(name) {
    if (name === 'pinia') return { defineStore: () => ({}) }
    if (name === '~/utils/roles') return roles
    return {}
  }
})

function guard(role, accessMode = null, clinicas = []) {
  const auth = {
    user: { role },
    isLoggedIn: true,
    isAdmin: role === 'admin',
    isMedico: role === 'medico',
    isAssistente: role === 'assistente',
    isRecepcao: roles.roleIn(role, roles.RECEPCAO_ROLES),
    canAccessFinanceiro: roles.roleIn(role, roles.FINANCEIRO_ROLES),
    accessMode,
    clinicas,
    activeClinicaId: null
  }
  return loadModule('../app/middleware/auth.global.ts', {
    require(name) {
      if (name === '~/utils/roles') return roles
      if (name === '~/stores/auth') return { ...authExports, useAuthStore: () => auth }
      throw new Error(`Unexpected import: ${name}`)
    },
    defineNuxtRouteMiddleware: handler => handler,
    navigateTo: path => path
  }).default
}

for (const role of ['financeiro', 'coord_financeiro', 'admin']) {
  test(`${role} can open all financial pages`, async () => {
    const middleware = guard(role, role === 'admin' ? 'financeiro' : null)
    for (const path of ['/financeiro/pagamentos', '/financeiro/pacientes/1', '/financeiro/conciliacao-cartoes']) {
      assert.equal(await middleware({ path }), undefined)
    }
  })
}

for (const role of ['medico', 'assistente', 'recepcao', 'coord_recepcao', 'dpo']) {
  test(`${role} cannot open financial pages`, async () => {
    const middleware = guard(role)
    for (const path of ['/financeiro/pagamentos', '/financeiro/pacientes/1', '/financeiro/conciliacao-cartoes']) {
      assert.equal(await middleware({ path }), '/acesso-negado')
    }
  })
}

test('financial users land on payments and cannot enter other work areas', async () => {
  for (const role of ['financeiro', 'coord_financeiro']) {
    const middleware = guard(role)
    for (const path of ['/', '/dashboard', '/recepcao', '/admin', '/lgpd/auditoria']) {
      const result = await middleware({ path })
      assert.equal(result, path === '/lgpd/auditoria' ? '/acesso-negado' : '/financeiro/pagamentos')
    }
  }
})

test('financial users can select a linked unit without requiring one for the prototype', async () => {
  const middleware = guard('financeiro', null, [{ id: 1 }, { id: 2 }])
  assert.equal(await middleware({ path: '/selecionar-clinica' }), undefined)
  assert.equal(await middleware({ path: '/financeiro/pagamentos' }), undefined)
})

test('admin financial mode has a destination and stays in the financial area', async () => {
  assert.equal(authExports.paginaInicialPorModo('financeiro'), '/financeiro/pagamentos')
  const middleware = guard('admin', 'financeiro')
  assert.equal(await middleware({ path: '/' }), '/financeiro/pagamentos')
  assert.equal(await middleware({ path: '/admin' }), '/financeiro/pagamentos')
  assert.equal(await middleware({ path: '/selecionar-acesso' }), undefined)
})

test('admin can also open financial pages from administrator mode', async () => {
  assert.equal(await guard('admin', 'administrador')({ path: '/financeiro/pagamentos' }), undefined)
})
