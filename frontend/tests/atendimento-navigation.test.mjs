import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { test } from 'node:test'
import { runInNewContext } from 'node:vm'
import ts from 'typescript'
import { createPinia, defineStore } from 'pinia'
import { computed, ref } from 'vue'

const paciente = {
  id: 12,
  clinicaId: 7,
  data: '2026-10-06',
  horario: '09:00',
  status: 'em-espera',
  paciente: { id: 34, nome: 'Paciente teste' }
}
const params = { chave: '10:7', clinicaId: 7, medicoId: 10 }

function deferred() {
  let resolve
  let reject
  const promise = new Promise((res, rej) => {
    resolve = res
    reject = rej
  })
  return { promise, resolve, reject }
}

// Execute the actual store/middleware with controlled HTTP and SSE ordering.
// Vue and Pinia remain real; no application implementation is duplicated here.
function loadModule(path, globals) {
  const source = readFileSync(new URL(path, import.meta.url), 'utf8')
    .replaceAll('import.meta.server', 'false')
  const { outputText } = ts.transpileModule(source, {
    compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022 }
  })
  const exports = {}
  runInNewContext(outputText, { exports, ...globals })
  return exports
}

function fixture(overrides = {}) {
  const handlers = new Map()
  let verificacoes = 0
  const services = {
    listarAgendamentos: async () => [{ ...paciente }],
    atualizarStatusAgendamento: async (id, status) => ({ ...paciente, id, status }),
    verificarAtendimentoEmAndamento: async () => {
      verificacoes++
      return { emAtendimento: false }
    },
    ...overrides
  }
  const { useAgendamentosStore } = loadModule('../app/features/agenda/stores/agendamentosStore.ts', {
    ref,
    computed,
    console: { error() {} },
    useSse: () => ({ on: (name, handler) => handlers.set(name, handler), connect() {} }),
    require: (name) => {
      if (name === 'pinia') return { defineStore }
      if (name === '../services/agendaService') return services
      if (name === '~/utils/time') return { normalizarHorario: value => value, minutosDoHorario: () => 0 }
      throw new Error(`Unexpected import: ${name}`)
    }
  })
  const store = useAgendamentosStore(createPinia())
  const navigate = async () => {
    const redirects = []
    const { default: middleware } = loadModule('../app/middleware/atendimento-ativo.ts', {
      defineNuxtRouteMiddleware: handler => handler,
      useAuthStore: () => ({ user: { id: 10 }, activeClinicaId: 7 }),
      useAgendamentosStore: () => store,
      useToast: () => ({ add() {} }),
      navigateTo: path => redirects.push(path)
    })
    await middleware()
    return redirects
  }
  return { store, handlers, navigate, verificacoes: () => verificacoes }
}

test('first navigation after Atender uses the successful PATCH without a second GET', async () => {
  const { store, navigate, verificacoes } = fixture()
  await store.init(7, paciente.data, 10, 'dashboard')
  await store.verificarAtendimentoAtual(params.chave)
  await store.atualizarStatus(paciente.id, 'em-atendimento', undefined, 7)
  assert.equal(store.emAtendimento.id, paciente.id)
  const before = verificacoes()
  assert.equal((await navigate()).length, 0)
  assert.equal(verificacoes(), before)
})

test('editing context survives a reload without the editing query parameter', async () => {
  const edicao = { ...paciente, status: 'em-atendimento', emEdicao: true }
  const { store, navigate } = fixture({
    listarAgendamentos: async () => [edicao],
    verificarAtendimentoEmAndamento: async () => ({
      emAtendimento: true, emEdicao: true, id: edicao.id, data: edicao.data, unidadeId: 7
    })
  })
  assert.equal((await navigate()).length, 0)
  assert.equal(store.emAtendimento.emEdicao, true)
  assert.equal(store.atendimentoAtualResumo.emEdicao, true)
})

test('cancelling editing applies the confirmed attended status and releases the active slot', async () => {
  const { store } = fixture({
    atualizarStatusAgendamento: async (id, status) => ({
      ...paciente, id, status: status === 'cancelado' ? 'atendido' : status, emEdicao: status === 'em-atendimento'
    })
  })
  await store.init(7, paciente.data, 10, 'dashboard')
  await store.atualizarStatus(paciente.id, 'em-atendimento', undefined, 7)
  assert.equal(store.emAtendimento.emEdicao, true)
  await store.atualizarStatus(paciente.id, 'cancelado', undefined, 7)
  assert.equal(store.emAtendimento, null)
  assert.equal(store.agendamentos[0].status, 'atendido')
  assert.equal(store.agendamentos[0].emEdicao, false)
  assert.equal(store.fila.length, 0)
})

test('authoritative active-appointment verification updates editing context in existing details', async () => {
  const { store } = fixture({
    listarAgendamentos: async () => [{ ...paciente, status: 'em-atendimento', emEdicao: false }],
    verificarAtendimentoEmAndamento: async () => ({
      emAtendimento: true, emEdicao: true, id: paciente.id, data: paciente.data, unidadeId: 7
    })
  })
  await store.init(7, paciente.data, 10, 'dashboard')
  await store.garantirAtendimentoAtual({ ...params, force: true })
  assert.equal(store.emAtendimento.emEdicao, true)
})

test('a fetch begun before the PATCH cannot overwrite the started appointment', async () => {
  const oldFetch = deferred()
  const { store } = fixture({ listarAgendamentos: () => oldFetch.promise })
  const fetch = store.fetchAgendamentos(7, paciente.data, 10, 'dashboard')
  await store.verificarAtendimentoAtual(params.chave)
  await store.atualizarStatus(paciente.id, 'em-atendimento', undefined, 7)
  oldFetch.resolve([{ ...paciente }])
  assert.equal(await fetch, 'cancelled')
  assert.equal(store.emAtendimento.id, paciente.id)
  assert.equal((await store.garantirAtendimentoAtual(params)).status, 'present')
})

test('old verification and snapshot during PATCH do not undo its result', async () => {
  const patch = deferred()
  const verification = deferred()
  const { store, handlers } = fixture({
    atualizarStatusAgendamento: () => patch.promise,
    verificarAtendimentoEmAndamento: () => verification.promise
  })
  await store.init(7, paciente.data, 10, 'dashboard')
  const checking = store.verificarAtendimentoAtual(params.chave)
  const starting = store.atualizarStatus(paciente.id, 'em-atendimento', undefined, 7)
  handlers.get('agenda:snapshot')({ data: paciente.data, contexto: 'dashboard', items: [] })
  patch.resolve({ ...paciente, status: 'em-atendimento' })
  await starting
  verification.resolve({ emAtendimento: false })
  assert.equal((await checking).status, 'cancelled')
  assert.equal(store.emAtendimento.id, paciente.id)
})

test('reload consults the backend and opens an active appointment', async () => {
  const { navigate } = fixture({
    verificarAtendimentoEmAndamento: async () => ({ emAtendimento: true, id: paciente.id, unidadeId: 7, data: paciente.data }),
    listarAgendamentos: async () => [{ ...paciente, status: 'em-atendimento' }]
  })
  assert.equal((await navigate()).length, 0)
})

test('direct access without an appointment redirects to dashboard', async () => {
  const { navigate, verificacoes } = fixture()
  assert.equal((await navigate())[0], '/dashboard')
  assert.equal(verificacoes(), 1)
})

test('a transient agenda failure preserves the existing appointment', async () => {
  let fail = false
  const { store } = fixture({ listarAgendamentos: async () => {
    if (fail) throw new Error('offline')
    return [{ ...paciente, status: 'em-atendimento' }]
  } })
  await store.init(7, paciente.data, 10, 'dashboard')
  fail = true
  assert.equal(await store.fetchAgendamentos(7, paciente.data, 10, 'dashboard'), 'error')
  assert.equal(store.emAtendimento.id, paciente.id)
})

test('remote confirmation with existing details does not reload the agenda', async () => {
  let fetches = 0
  const { store } = fixture({
    listarAgendamentos: async () => {
      fetches++
      return [{ ...paciente, status: 'em-atendimento' }]
    },
    verificarAtendimentoEmAndamento: async () => ({ emAtendimento: true, id: paciente.id, unidadeId: 7, data: paciente.data })
  })
  await store.init(7, paciente.data, 10, 'dashboard')
  const before = fetches
  assert.equal((await store.garantirAtendimentoAtual({ ...params, force: true })).status, 'present')
  assert.equal(fetches, before)
})

test('a late snapshot preserves the PATCH until authoritative revalidation completes', async () => {
  const verification = deferred()
  const { store, handlers } = fixture({ verificarAtendimentoEmAndamento: () => verification.promise })
  await store.init(7, paciente.data, 10, 'dashboard')
  const checking = store.verificarAtendimentoAtual(params.chave)
  await store.atualizarStatus(paciente.id, 'em-atendimento', undefined, 7)
  handlers.get('agenda:snapshot')({ data: paciente.data, contexto: 'dashboard', items: [{ ...paciente }] })
  assert.equal(store.emAtendimento.id, paciente.id)
  verification.resolve({ emAtendimento: true, id: paciente.id, unidadeId: 7, data: paciente.data })
  await checking
  assert.equal((await store.garantirAtendimentoAtual(params)).status, 'present')
})

test('a failed PATCH releases mutation state so verification can be retried', async () => {
  const { store } = fixture({ atualizarStatusAgendamento: async () => {
    throw new Error('offline')
  } })
  await assert.rejects(store.atualizarStatus(paciente.id, 'em-atendimento', undefined, 7))
  assert.equal((await store.verificarAtendimentoAtual(params.chave, true)).status, 'absent')
  assert.equal(store.loading, false)
})

test('changing user/unit context discards pending agenda responses', async () => {
  const pending = deferred()
  const { store } = fixture({ listarAgendamentos: () => pending.promise })
  const fetching = store.fetchAgendamentos(7, paciente.data, 10, 'dashboard')
  store.invalidarAtendimentoAtual()
  pending.resolve([{ ...paciente, status: 'em-atendimento' }])
  assert.equal(await fetching, 'cancelled')
  assert.equal(store.emAtendimento, null)
})

function encerramentoFixture(resultado, navigationFails = false) {
  const source = readFileSync(new URL('../app/pages/atendimento-medico.vue', import.meta.url), 'utf8')
    .split('<script setup lang="ts">')[1].split('</script>')[0]
  const parsed = ts.createSourceFile('page.ts', source, ts.ScriptTarget.Latest, true)
  const names = ['reconciliarFalhaEncerramento', 'cancelarAtendimento']
  const functions = parsed.statements.filter(node => ts.isFunctionDeclaration(node) && names.includes(node.name?.text))
  const snippet = `${functions.map(node => node.getText(parsed)).join('\n')}\nexport { ${names.join(', ')} }`
  const { outputText } = ts.transpileModule(snippet, {
    compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022 }
  })
  let limpezas = 0
  let saidas = 0
  const globals = {
    exports: {},
    auth: { user: { id: 10 }, activeClinicaId: 7 },
    agendamentosStore: {
      emAtendimento: resultado.status === 'present' ? { ...paciente, id: resultado.resumo.id } : null,
      verificarAtendimentoAtual: async () => resultado,
      atualizarStatus: async () => { throw new Error('response lost') }
    },
    agendamento: ref({ ...paciente }),
    encerramentoEmAndamento: ref(null),
    cancelandoConsulta: ref(false),
    modalCancelarAberto: ref(true),
    draftKey: ref('draft:12:34'),
    draftDesativado: false,
    cronometro: { stop() {} },
    console: { error() {} },
    toast: { add() {} },
    atendimentoPermiteMutacao: () => true,
    salvarDraftAgora() {},
    limparDraft: () => limpezas++,
    liberarSaida() {},
    navigateTo: async () => {
      saidas++
      if (navigationFails) throw new Error('navigation failed')
    }
  }
  runInNewContext(outputText, globals)
  return { globals, limpezas: () => limpezas, saidas: () => saidas }
}

test('PATCH failure plus absence preserves draft instead of asserting successful saving', async () => {
  const { globals, limpezas, saidas } = encerramentoFixture({ status: 'absent' })
  await globals.exports.cancelarAtendimento()
  assert.equal(limpezas(), 0)
  assert.equal(globals.draftDesativado, true)
  assert.equal(saidas(), 1)
  assert.equal(globals.encerramentoEmAndamento.value, null)
})

test('another active patient cannot receive the original draft', async () => {
  const { globals, limpezas, saidas } = encerramentoFixture({ status: 'present', resumo: { id: 99 } })
  await globals.exports.cancelarAtendimento()
  assert.equal(globals.agendamento.value.id, paciente.id)
  assert.equal(globals.draftDesativado, true)
  assert.equal(limpezas(), 0)
  assert.equal(saidas(), 1)
})

test('failed navigation during reconciliation always releases action flags', async () => {
  const { globals } = encerramentoFixture({ status: 'absent' }, true)
  await assert.rejects(globals.exports.cancelarAtendimento())
  assert.equal(globals.encerramentoEmAndamento.value, null)
  assert.equal(globals.cancelandoConsulta.value, false)
})
