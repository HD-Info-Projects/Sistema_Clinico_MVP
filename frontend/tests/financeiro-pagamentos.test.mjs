import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { test } from 'node:test'
import { runInNewContext } from 'node:vm'
import ts from 'typescript'
import { computed, nextTick, reactive, ref, watch } from 'vue'

const cache = new Map()
function loadModule(url) {
  if (cache.has(url.href)) return cache.get(url.href)
  const source = readFileSync(url, 'utf8')
  const { outputText } = ts.transpileModule(source, {
    compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022 }
  })
  const exports = {}
  cache.set(url.href, exports)
  runInNewContext(outputText, {
    exports,
    Date,
    Error,
    require(name) {
      if (name.startsWith('.')) return loadModule(new URL(`${name}.ts`, url))
      throw new Error(`Unexpected import: ${name}`)
    }
  })
  return exports
}

const { resolverPeriodoPagamento, validarIntervaloPagamento } = loadModule(new URL('../app/features/financeiro/utils/periodos.ts', import.meta.url))
const { criarPagamentosMock } = loadModule(new URL('../app/features/financeiro/mocks/pagamentos.ts', import.meta.url))
const { listarPagamentos } = loadModule(new URL('../app/features/financeiro/services/financeiroService.ts', import.meta.url))
const { formatarCpf } = loadModule(new URL('../app/utils/masks.ts', import.meta.url))
const referencia = new Date(2026, 9, 9, 12)
const baseConsulta = { unidadeId: 1, dataIni: '2026-09-01', dataFim: '2026-10-31', page: 1, pageSize: 20 }

test('preset periods use inclusive calendar dates across month and year boundaries', () => {
  const january = new Date(2026, 0, 1, 23, 30)
  for (const [preset, dataIni, dataFim] of [
    ['hoje', '2026-01-01', '2026-01-01'],
    ['ontem', '2025-12-31', '2025-12-31'],
    ['ultimos-7-dias', '2025-12-26', '2026-01-01'],
    ['este-mes', '2026-01-01', '2026-01-31'],
    ['mes-anterior', '2025-12-01', '2025-12-31']
  ]) {
    const intervalo = resolverPeriodoPagamento(preset, {}, january)
    assert.equal(intervalo.dataIni, dataIni)
    assert.equal(intervalo.dataFim, dataFim)
  }
  assert.equal(resolverPeriodoPagamento('mes-anterior', {}, new Date(2024, 2, 1)).dataFim, '2024-02-29')
})

test('custom dates accept a single day and reject missing, impossible and inverted intervals', () => {
  const custom = { dataIni: '2024-02-29', dataFim: '2024-02-29' }
  assert.equal(validarIntervaloPagamento(custom.dataIni, custom.dataFim), null)
  assert.equal(resolverPeriodoPagamento('personalizado', custom).dataIni, custom.dataIni)
  for (const [dataIni, dataFim] of [
    ['', '2026-10-09'],
    ['2026-10-09', ''],
    ['2026-02-29', '2026-03-01'],
    ['2026-10-10', '2026-10-09']
  ]) {
    assert.notEqual(validarIntervaloPagamento(dataIni, dataFim), null)
    assert.throws(() => resolverPeriodoPagamento('personalizado', { dataIni, dataFim }))
  }
})

test('cards describe the entire filtered result, independent of pagination', async () => {
  const all = await listarPagamentos({ ...baseConsulta, pageSize: 200 }, referencia)
  const first = await listarPagamentos(baseConsulta, referencia)
  const second = await listarPagamentos({ ...baseConsulta, page: 2 }, referencia)
  assert.ok(first.total > 20)
  assert.equal(first.items.length, 20)
  assert.equal(new Set([...first.items, ...second.items].map(item => item.id)).size, 40)
  assert.equal(JSON.stringify(first.resumo), JSON.stringify(second.resumo))
  assert.equal(first.resumo.conciliados + first.resumo.pendentes + first.resumo.divergentes, all.total)
  assert.equal(first.resumo.totalBrutoCentavos, all.items.reduce((sum, item) => sum + item.valorBrutoCentavos, 0))
  assert.ok(all.items.every(item => Number.isInteger(item.valorBrutoCentavos)))
  for (let index = 1; index < all.items.length; index++) {
    assert.ok(all.items[index - 1].data >= all.items[index].data)
  }
})

test('name, masked CPF, status and period filters combine and recalculate the cards', async () => {
  const pagamentos = criarPagamentosMock(1, referencia)
  const paciente = pagamentos.find(item => item.paciente.nome === 'João Pereira').paciente
  const cpf = formatarCpf(paciente.cpf)
  const consulta = { ...baseConsulta, paciente: ' joao ', cpf, status: 'pendente', dataIni: '2026-10-09', dataFim: '2026-10-09' }
  const resultado = await listarPagamentos(consulta, referencia)
  assert.ok(resultado.total > 0)
  assert.ok(resultado.items.every(item => item.paciente.id === paciente.id && item.status === 'pendente' && item.data === consulta.dataIni))
  assert.equal(resultado.resumo.pendentes, resultado.total)
  assert.equal(resultado.resumo.conciliados, 0)
  assert.equal(resultado.resumo.divergentes, 0)
  const semMascara = await listarPagamentos({ ...consulta, cpf: paciente.cpf }, referencia)
  assert.equal(JSON.stringify(semMascara), JSON.stringify(resultado))
  const vazio = await listarPagamentos({ ...consulta, paciente: 'Paciente inexistente', page: 9 }, referencia)
  assert.equal(vazio.total, 0)
  assert.equal(vazio.page, 1)
  assert.equal(vazio.resumo.totalBrutoCentavos, 0)
})

test('mock payments stay within the selected unit and include all payment methods and statuses', async () => {
  const first = await listarPagamentos({ ...baseConsulta, pageSize: 200 }, referencia)
  const second = await listarPagamentos({ ...baseConsulta, unidadeId: 2, pageSize: 200 }, referencia)
  assert.ok(first.items.every(item => item.unidadeId === 1))
  assert.ok(second.items.every(item => item.unidadeId === 2))
  const pacientes = new Set(first.items.map(item => item.paciente.id))
  assert.ok(second.items.every(item => !pacientes.has(item.paciente.id)))
  assert.equal(new Set(first.items.map(item => item.formaPagamento)).size, 4)
  assert.equal(new Set(first.items.map(item => item.status)).size, 3)
  await assert.rejects(listarPagamentos({ ...baseConsulta, unidadeId: 0 }, referencia), /Selecione uma unidade/)
  await assert.rejects(listarPagamentos({ ...baseConsulta, page: 0 }, referencia), /Paginação inválida/)
  const ultima = await listarPagamentos({ ...baseConsulta, page: 999 }, referencia)
  assert.equal(ultima.page, Math.ceil(ultima.total / baseConsulta.pageSize))
})

function pageFixture(load = query => listarPagamentos(query, referencia)) {
  const source = readFileSync(new URL('../app/pages/financeiro/pagamentos.vue', import.meta.url), 'utf8')
    .split('<script setup lang="ts">')[1].split('</script>')[0]
  const { outputText } = ts.transpileModule(`${source}\nexport { dados, filtros, page, loading, errorMsg, aplicarFiltros, mudarPagina }`, {
    compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022 }
  })
  const auth = reactive({ activeClinicaId: 1, user: { nome: 'Financeiro teste' } })
  const exports = {}
  const stops = []
  let mount
  let unmount
  runInNewContext(outputText, {
    exports, Date, Error, ref, computed,
    watch: (...args) => { stops.push(watch(...args)) },
    definePageMeta() {},
    inject: () => () => {},
    useAuthStore: () => auth,
    onMounted: (callback) => { mount = callback },
    onBeforeUnmount: (callback) => { unmount = callback },
    require(name) {
      if (name.endsWith('financeiroService')) return { listarPagamentos: load }
      if (name.endsWith('periodos')) return {
        resolverPeriodoPagamento: (preset, custom) => resolverPeriodoPagamento(preset, custom, referencia)
      }
      if (name === '~/utils/masks') return { formatarCpf }
      throw new Error(`Unexpected import: ${name}`)
    }
  })
  mount()
  return {
    ...exports,
    auth,
    dispose() {
      unmount()
      stops.forEach(stop => stop())
    }
  }
}

async function flush() {
  await nextTick()
  await new Promise(resolve => setImmediate(resolve))
}

test('page applies filters explicitly, resets pagination and keeps the same totals on page changes', async (t) => {
  const page = pageFixture()
  t.after(() => page.dispose())
  await flush()
  assert.ok(page.dados.value.total > 20)
  const total = page.dados.value.resumo.totalBrutoCentavos
  page.mudarPagina(2)
  await flush()
  assert.equal(page.page.value, 2)
  assert.equal(page.dados.value.resumo.totalBrutoCentavos, total)
  page.filtros.value.status = 'pendente'
  assert.ok(page.dados.value.items.some(item => item.status !== 'pendente'))
  page.aplicarFiltros()
  await flush()
  assert.equal(page.page.value, 1)
  assert.ok(page.dados.value.items.every(item => item.status === 'pendente'))
  assert.equal(page.dados.value.resumo.conciliados, 0)
})

test('a late response from the previous unit cannot replace the new unit data', async (t) => {
  const requests = []
  const page = pageFixture(query => new Promise(resolve => requests.push({ query, resolve })))
  t.after(() => page.dispose())
  const previous = requests[0]
  page.auth.activeClinicaId = 2
  await flush()
  assert.equal(requests.length, 2)
  const current = requests[1]
  current.resolve(await listarPagamentos(current.query, referencia))
  await flush()
  assert.ok(page.dados.value.items.every(item => item.unidadeId === 2))
  previous.resolve(await listarPagamentos(previous.query, referencia))
  await flush()
  assert.ok(page.dados.value.items.every(item => item.unidadeId === 2))
  assert.equal(page.loading.value, false)
})

test('service failures clear the data and provide an error, then filters can retry', async (t) => {
  let fail = true
  const page = pageFixture(query => fail ? Promise.reject(new Error('Erro de teste')) : listarPagamentos(query, referencia))
  t.after(() => page.dispose())
  await flush()
  assert.equal(page.errorMsg.value, 'Erro de teste')
  assert.equal(page.dados.value.total, 0)
  assert.equal(page.loading.value, false)
  fail = false
  page.aplicarFiltros()
  await flush()
  assert.equal(page.errorMsg.value, '')
  assert.ok(page.dados.value.total > 0)
})
