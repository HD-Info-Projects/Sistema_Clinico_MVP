import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { test } from 'node:test'
import { runInNewContext } from 'node:vm'
import ts from 'typescript'
import { computed, nextTick, ref, watch } from 'vue'

const source = readFileSync(new URL('../app/pages/atendimento-medico.vue', import.meta.url), 'utf8')
const script = source.split('<script setup lang="ts">')[1].split('</script>')[0]
const parsed = ts.createSourceFile('page.ts', script, ts.ScriptTarget.Latest, true)
const salvo = {
  spdata_atendimento_id: 34,
  anamnese: '<p>Anamnese e evolução salvas</p>',
  cid_principal: 'J06.9',
  cid_principal_descricao: 'Infecção aguda',
  cids_secundarios: [{ codigo: 'R50.9', descricao: 'Febre' }],
  medicamentos: ['Medicamento A — 1 comprimido ao dia'],
  exames: [{ nome: 'Hemograma', exame_id: 45, codigo_amb: '40304361', codigo_alfanumerico: 'HEM', orientacao: '<p>Jejum de 8 horas</p>' }],
  cid_personalizado: 'Z00.0',
  cid_personalizado_descricao: 'Exame médico geral'
}

function fixture(savedDraft, load, options = {}) {
  const storage = new Map()
  const key = 'medsystem:atendimento-draft:edicao:12:34'
  if (savedDraft) storage.set(key, JSON.stringify({ version: 6, savedAt: new Date().toISOString(), ...savedDraft }))
  const local = new Map()
  const timers = new Set()
  const stops = []
  const mutations = []
  const requests = []
  const navigations = []
  const toasts = []
  const context = {
    ref, computed, nextTick, AbortController,
    watch: (...args) => {
      const stop = watch(...args)
      stops.push(stop)
      return stop
    },
    setTimeout: (callback, delay) => {
      const timer = setTimeout(callback, delay)
      timers.add(timer)
      return timer
    },
    clearTimeout,
    sessionStorage: {
      getItem: key => storage.get(key),
      setItem: (key, value) => storage.set(key, value),
      removeItem: key => storage.delete(key)
    },
    localStorage: { removeItem: key => local.delete(key) },
    agendamento: ref({ id: 12, clinicaId: 7, spdataAtendimentoId: 34, paciente: { id: 34 }, emEdicao: true, ...options.agendamento }),
    encerramentoEmAndamento: ref(options.previousEnding ?? null),
    saidaLiberada: ref(options.previousExit ?? false),
    destinoPendente: ref('/dashboard'),
    finalizandoConsulta: ref(false),
    cancelandoConsulta: ref(false),
    modalCancelarAberto: ref(false),
    modalSairAberto: ref(false),
    cronometro: { elapsed: 999, stop() {} },
    agendamentosStore: {
      atualizarStatus: async (...args) => mutations.push(JSON.parse(JSON.stringify(args)))
    },
    atendimentoPermiteMutacao: () => true,
    validarCidPersonalizado: () => true,
    navigateTo: async path => navigations.push(path),
    loadConsulta: load,
    $fetch: async (url, config) => {
      requests.push({ url, config })
      return options.fetch ? options.fetch(url, config) : [salvo]
    },
    toast: { add: toast => toasts.push(toast) },
    console: { error() {} },
    exports: {}
  }
  context.resetarSaida = () => {
    context.saidaLiberada.value = false
    context.encerramentoEmAndamento.value = null
    context.destinoPendente.value = null
  }
  context.liberarSaida = () => {
    context.saidaLiberada.value = true
  }
  for (const name of ['tabAtiva', 'anamneseTexto', 'searchCid', 'receitaTexto', 'remedioNome', 'remedioDosagem', 'remedioDetalhes', 'buscaTermoExame', 'searchCidPersonalizado']) {
    context[name] = ref('')
  }
  for (const name of ['cidSelecionadoLista', 'examesSelecionados']) context[name] = ref([])
  for (const name of ['exameSelecionado', 'cidPersonalizadoSelecionado']) context[name] = ref(null)
  for (const name of ['caraterAtendimento', 'usarCidPersonalizado']) context[name] = ref(false)
  context.cidPrincipalIndex = ref(0)
  const functions = source.slice(source.indexOf('const draftSalvoEm ='), source.indexOf('watch(\n  [\n    tabAtiva'))
  const initialization = source.slice(source.indexOf('watch(\n  draftKey,'), source.indexOf('onMounted(() => {\n  window.addEventListener'))
  const entry = source.slice(source.indexOf('// A entrada precisa'), source.indexOf('const modalSairAberto'))
  const state = source.slice(source.indexOf('const modoEdicao ='), source.indexOf('async function carregarConsultaExistente'))
  const names = ['normalizarIdExame', 'normalizarExameSelecionado', 'normalizarListaExames', 'htmlTemConteudo', 'exameExisteNaLista', 'finalizarConsulta', 'finalizarPeloModalSaida', 'pausarAtendimento', 'cancelarAtendimento']
  if (!load) names.push('carregarConsultaExistente')
  const actualFunctions = parsed.statements
    .filter(node => ts.isFunctionDeclaration(node) && names.includes(node.name?.text))
    .map(node => node.getText(parsed)).join('\n')
  const loadStub = load ? 'const carregarConsultaExistente = loadConsulta' : ''
  const code = `${entry}\n${state}\n${actualFunctions}\n${loadStub}\n${functions}\n${initialization}\nexports = { modoEdicao, carregandoEdicao, falhaCargaEdicao, edicaoCarregada, finalizacaoBloqueada, draftKey, salvarDraftAgora, limparDraft, salvarDraftComDebounce, finalizarConsulta, finalizarPeloModalSaida, pausarAtendimento, cancelarAtendimento }`
    .replaceAll('import.meta.client', 'true')
  const { outputText } = ts.transpileModule(code, {
    compilerOptions: { target: ts.ScriptTarget.ES2022, module: ts.ModuleKind.CommonJS }
  })
  runInNewContext(outputText, context)
  Object.assign(context, context.exports)
  return {
    context, storage, key, mutations, requests, navigations, toasts,
    cleanup: () => {
      stops.forEach(stop => stop())
      timers.forEach(timer => clearTimeout(timer))
    }
  }
}

test('editing loads saved clinical data before restoring the paused draft', async () => {
  let resolve
  const load = new Promise((done) => {
    resolve = done
  })
  const f = fixture({ anamneseTexto: 'Edição pausada', medicamentos: [] }, () => load)
  try {
    assert.equal(f.context.carregandoEdicao.value, true)
    f.context.anamneseTexto.value = 'Consulta original'
    f.context.exports.salvarDraftAgora()
    assert.equal(JSON.parse(f.storage.get(f.key)).anamneseTexto, 'Edição pausada')
    resolve(true)
    await new Promise(setImmediate)
    await nextTick()
    await nextTick()
    assert.equal(f.context.anamneseTexto.value, 'Edição pausada')
    assert.equal(f.context.carregandoEdicao.value, false)
    assert.notEqual(f.context.exports.draftKey.value, 'medsystem:atendimento-draft:12:34')
  } finally {
    f.cleanup()
  }
})

test('an editing draft preserves deliberately cleared fields and is not recreated after discard', async () => {
  const f = fixture()
  try {
    await new Promise(setImmediate)
    await nextTick()
    await nextTick()
    f.context.anamneseTexto.value = ''
    f.context.receitaTexto.value = ''
    f.context.cidSelecionadoLista.value = []
    f.context.examesSelecionados.value = []
    f.context.usarCidPersonalizado.value = false
    f.context.cidPersonalizadoSelecionado.value = null
    f.context.exports.salvarDraftAgora()
    assert.equal(JSON.parse(f.storage.get(f.key)).anamneseTexto, '')
    f.context.exports.limparDraft()
    f.context.exports.salvarDraftComDebounce()
    f.context.exports.salvarDraftAgora()
    assert.equal(f.storage.has(f.key), false)
  } finally {
    f.cleanup()
  }
})

test('failed loading preserves the paused draft instead of overwriting it with empty fields', async () => {
  const f = fixture({ anamneseTexto: 'Rascunho preservado' }, async () => false)
  try {
    await new Promise(setImmediate)
    await nextTick()
    await nextTick()
    f.context.exports.salvarDraftAgora()
    assert.equal(f.context.falhaCargaEdicao.value, true)
    assert.equal(JSON.parse(f.storage.get(f.key)).anamneseTexto, 'Rascunho preservado')
  } finally {
    f.cleanup()
  }
})

for (const previousEnding of [null, 'finalizar', 'cancelar']) {
  test(`editing after leaving an appointment resets shared exit state and loads all saved fields (${previousEnding})`, async () => {
    const f = fixture(undefined, undefined, { previousExit: true, previousEnding })
    try {
      assert.equal(f.context.saidaLiberada.value, false)
      assert.equal(f.context.encerramentoEmAndamento.value, null)
      assert.equal(f.context.finalizacaoBloqueada.value, true)
      await new Promise(setImmediate)
      assert.equal(f.requests.length, 1)
      assert.equal(f.requests[0].config.query.spdataAtendimentoId, 34)
      assert.equal(f.context.anamneseTexto.value, salvo.anamnese)
      assert.equal(f.context.receitaTexto.value, salvo.medicamentos.join('\n'))
      assert.equal(f.context.cidSelecionadoLista.value.length, 2)
      assert.equal(f.context.cidSelecionadoLista.value[0].cid, salvo.cid_principal)
      assert.equal(f.context.cidSelecionadoLista.value[1].cid, 'R50.9')
      assert.equal(f.context.examesSelecionados.value[0].exameId, 45)
      assert.equal(f.context.examesSelecionados.value[0].orientacao, salvo.exames[0].orientacao)
      assert.equal(f.context.cidPersonalizadoSelecionado.value.cid, salvo.cid_personalizado)
      assert.equal(f.context.edicaoCarregada.value, true)
      assert.equal(f.context.finalizacaoBloqueada.value, false)
    } finally {
      f.cleanup()
    }
  })
}

test('finalizing an unchanged edit submits the saved clinical content rather than empty fields', async () => {
  const f = fixture(undefined, undefined, { previousExit: true })
  try {
    await new Promise(setImmediate)
    await f.context.finalizarConsulta()
    assert.equal(f.mutations.length, 1)
    const [id, status, payload, clinicaId] = f.mutations[0]
    assert.equal(id, 12)
    assert.equal(status, 'atendido')
    assert.equal(clinicaId, 7)
    assert.equal(payload.anamnese, salvo.anamnese)
    assert.equal(payload.medicamentos, salvo.medicamentos.join('\n'))
    assert.deepEqual(payload.diagnosticos, [
      { cid: 'J06.9', descricao: 'Infecção aguda', principal: true },
      { cid: 'R50.9', descricao: 'Febre', principal: false }
    ])
    assert.deepEqual(payload.exames, salvo.exames)
    assert.deepEqual(payload.cid_personalizado, { cid: 'Z00.0', descricao: 'Exame médico geral' })
    assert.equal('duracao' in payload, false)
    assert.equal(f.storage.has(f.key), false)
    assert.deepEqual(f.navigations, ['/dashboard'])
  } finally {
    f.cleanup()
  }
})

test('neither completion entry point can save while loading is pending', async () => {
  let resolve
  const pending = new Promise((done) => {
    resolve = done
  })
  const f = fixture(undefined, undefined, { fetch: () => pending })
  try {
    await f.context.finalizarConsulta()
    await f.context.finalizarPeloModalSaida()
    assert.equal(f.mutations.length, 0)
    assert.equal(f.context.edicaoCarregada.value, false)
    assert.equal(f.context.finalizacaoBloqueada.value, true)
    resolve([salvo])
    await new Promise(setImmediate)
    assert.equal(f.context.finalizacaoBloqueada.value, false)
  } finally {
    f.cleanup()
  }
})

test('explicitly clearing loaded fields remains a valid edit', async () => {
  const f = fixture()
  try {
    await new Promise(setImmediate)
    f.context.anamneseTexto.value = ''
    f.context.receitaTexto.value = ''
    f.context.cidSelecionadoLista.value = []
    f.context.examesSelecionados.value = []
    f.context.usarCidPersonalizado.value = false
    f.context.cidPersonalizadoSelecionado.value = null
    await f.context.finalizarConsulta()
    assert.equal(f.mutations.length, 1)
    assert.equal(f.mutations[0][2].anamnese, '')
    assert.equal(f.mutations[0][2].medicamentos, '')
    assert.deepEqual(f.mutations[0][2].diagnosticos, [])
    assert.deepEqual(f.mutations[0][2].exames, [])
  } finally {
    f.cleanup()
  }
})

test('completion is blocked if initialization was skipped even without a loading or error flag', async () => {
  const f = fixture()
  try {
    await new Promise(setImmediate)
    f.context.edicaoCarregada.value = false
    f.context.carregandoEdicao.value = false
    f.context.falhaCargaEdicao.value = false
    await f.context.finalizarConsulta()
    await f.context.finalizarPeloModalSaida()
    assert.equal(f.context.finalizacaoBloqueada.value, true)
    assert.equal(f.mutations.length, 0)
  } finally {
    f.cleanup()
  }
})

for (const failure of ['request failed', 'record missing', 'wrong appointment', 'missing identifier']) {
  test(`failed clinical loading blocks completion but permits cancellation (${failure})`, async () => {
    const f = fixture(undefined, undefined, {
      agendamento: failure === 'missing identifier' ? { spdataAtendimentoId: null } : {},
      fetch: async () => {
        if (failure === 'request failed') throw new Error('Network unavailable')
        return failure === 'wrong appointment' ? [{ ...salvo, spdata_atendimento_id: 99 }] : []
      }
    })
    try {
      await new Promise(setImmediate)
      assert.equal(f.context.falhaCargaEdicao.value, true)
      assert.equal(f.context.finalizacaoBloqueada.value, true)
      await f.context.finalizarConsulta()
      await f.context.finalizarPeloModalSaida()
      assert.equal(f.mutations.length, 0)
      await f.context.cancelarAtendimento()
      assert.equal(f.mutations.length, 1)
      assert.equal(f.mutations[0][1], 'cancelado')
      assert.equal(f.mutations[0][2], null)
    } finally {
      f.cleanup()
    }
  })
}

test('resuming a paused edit loads saved content and then restores the pending changes', async () => {
  const f = fixture({ anamneseTexto: 'Evolução editada ainda não finalizada', examesSelecionados: salvo.exames }, undefined, { previousExit: true })
  try {
    await new Promise(setImmediate)
    assert.equal(f.requests.length, 1)
    assert.equal(f.context.anamneseTexto.value, 'Evolução editada ainda não finalizada')
    assert.equal(f.context.examesSelecionados.value[0].orientacao, salvo.exames[0].orientacao)
    assert.equal(f.context.finalizacaoBloqueada.value, false)
  } finally {
    f.cleanup()
  }
})

test('a late response after leaving editing cannot populate fields or unlock completion', async () => {
  let resolve
  const pending = new Promise((done) => {
    resolve = done
  })
  const f = fixture(undefined, undefined, { fetch: () => pending })
  f.cleanup()
  resolve([salvo])
  await new Promise(setImmediate)
  assert.equal(f.context.anamneseTexto.value, '')
  assert.equal(f.context.edicaoCarregada.value, false)
  assert.equal(f.context.finalizacaoBloqueada.value, true)
  assert.equal(f.toasts.length, 0)
})
