import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { test } from 'node:test'
import { runInNewContext } from 'node:vm'
import ts from 'typescript'
import { createPinia, defineStore, setActivePinia } from 'pinia'
import { computed, ref, watch } from 'vue'
import { z } from 'zod'

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

function guard(role, accessMode = null, clinicas = [{ id: 1 }], activeClinicaId = 1) {
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
    activeClinicaId
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

test('financial users must choose a unit before opening financial pages', async () => {
  for (const role of ['financeiro', 'coord_financeiro', 'admin']) {
    for (const clinicas of [[], [{ id: 1 }], [{ id: 1 }, { id: 2 }]]) {
      const middleware = guard(role, role === 'admin' ? 'financeiro' : null, clinicas, null)
      assert.equal(await middleware({ path: '/selecionar-clinica' }), undefined)
      for (const path of ['/financeiro/pagamentos', '/financeiro/pacientes/1', '/financeiro/conciliacao-cartoes']) {
        assert.equal(await middleware({ path }), '/selecionar-clinica')
      }
    }
  }
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
  assert.equal(await guard('admin', 'administrador', [{ id: 1 }], null)({ path: '/financeiro/pagamentos' }), '/selecionar-clinica')
})

test('financial login selects a single unit automatically and asks when multiple or none are available', async () => {
  for (const role of ['financeiro', 'coord_financeiro']) {
    for (const clinicas of [[], [{ id: 1 }], [{ id: 1 }, { id: 2 }]]) {
      setActivePinia(createPinia())
      const destinations = []
      const { useAuthStore } = loadModule('../app/stores/auth.ts', {
        ref,
        computed,
        watch,
        useRuntimeConfig: () => ({ public: { authCookieMaxAgeSeconds: 3600 } }),
        useCookie: () => ref(null),
        navigateTo: path => destinations.push(path),
        require(name) {
          if (name === 'pinia') return { defineStore }
          if (name === '~/utils/roles') return roles
          if (name === '~/features/auth/services/authService') {
            return { loginAuth: async () => ({ user: { id: 7, role }, clinicas, activeClinicaId: null }) }
          }
          return {}
        }
      })
      const auth = useAuthStore()
      const result = await auth.login({ username: 'financeiro', password: 'senha-teste' })
      assert.equal(result.success, true)
      assert.equal(auth.activeClinicaId, clinicas.length === 1 ? 1 : null)
      assert.equal(destinations.at(-1), clinicas.length === 1 ? '/financeiro/pagamentos' : '/selecionar-clinica')
    }
  }
})

async function pageScript(path, globals) {
  const source = readFileSync(new URL(path, import.meta.url), 'utf8').match(/<script setup lang="ts">([\s\S]*?)<\/script>/)[1]
    .replaceAll('import.meta.client', 'true')
  const { outputText } = ts.transpileModule(`${source}\nexport { selecionar }`, {
    compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022 }
  })
  const exports = {}
  await runInNewContext(`(async () => { ${outputText} })()`, {
    exports,
    require(name) {
      if (name === '~/stores/auth') return authExports
      if (name === '~/utils/auditoria-eventos') return { registrarEventoAuditoria() {} }
      throw new Error(`Unexpected import: ${name}`)
    },
    ...globals
  })
  return exports
}

test('choosing financial access asks the admin to choose among multiple units, even with a previous selection', async () => {
  for (const activeClinicaId of [null, 1]) {
    const destinations = []
    const auth = {
      user: { role: 'admin' },
      clinicas: [{ id: 1 }, { id: 2 }],
      activeClinicaId,
      setAccessMode(mode) { this.accessMode = mode }
    }
    const page = await pageScript('../app/pages/selecionar-acesso.vue', {
      useAuthStore: () => auth,
      navigateTo: path => destinations.push(path)
    })
    page.selecionar('financeiro')
    assert.equal(auth.accessMode, 'financeiro')
    assert.equal(destinations.at(-1), '/selecionar-clinica')
  }
})

test('choosing financial access opens payments directly with a single active unit', async () => {
  const destinations = []
  const page = await pageScript('../app/pages/selecionar-acesso.vue', {
    useAuthStore: () => ({ user: { role: 'admin' }, clinicas: [{ id: 1 }], activeClinicaId: 1, setAccessMode() {} }),
    navigateTo: path => destinations.push(path)
  })
  page.selecionar('financeiro')
  assert.equal(destinations.at(-1), '/financeiro/pagamentos')
})

test('selecting a unit returns all financial profiles to payments only after confirmation', async () => {
  for (const role of ['financeiro', 'coord_financeiro', 'admin']) {
    for (const success of [false, true]) {
      const destinations = []
      const auth = {
        isAdmin: role === 'admin', isRecepcao: role === 'admin', canAccessFinanceiro: true,
        accessMode: role === 'admin' ? 'financeiro' : null,
        async setActiveClinica(id) {
          assert.equal(id, 2)
          return success
        }
      }
      const page = await pageScript('../app/pages/selecionar-clinica.vue', {
        ref,
        computed,
        useAuthStore: () => auth,
        navigateTo: path => destinations.push(path)
      })
      await page.selecionar(2)
      assert.equal(destinations.at(-1), success ? '/financeiro/pagamentos' : undefined)
    }
  }
})

test('financial user creation requires a unit in both form rules and server validation', () => {
  const serverRoles = loadModule('../server/utils/roles.ts')
  const { criarUsuarioSchema, atualizarUsuarioSchema } = loadModule('../server/features/usuarios/schema.ts', {
    require(name) {
      if (name === 'zod') return { z }
      if (name === '../../utils/roles') return serverRoles
      throw new Error(`Unexpected import: ${name}`)
    }
  })
  for (const role of ['financeiro', 'coord_financeiro']) {
    const body = { role, nome_completo: 'Financeiro teste', cnpj_cpf: '00000000000', username: 'financeiro.teste', senha: 'senha-teste' }
    assert.equal(roles.roleExigeUnidade(role), true)
    assert.equal(criarUsuarioSchema.safeParse(body).success, false)
    assert.equal(criarUsuarioSchema.safeParse({ ...body, unidade_ids: [] }).success, false)
    assert.equal(criarUsuarioSchema.safeParse({ ...body, unidade_ids: [1] }).success, true)
    assert.equal(atualizarUsuarioSchema.safeParse({ role, unidade_ids: [] }).success, false)
    assert.equal(atualizarUsuarioSchema.safeParse({ role, unidade_ids: [1] }).success, true)
  }
})
