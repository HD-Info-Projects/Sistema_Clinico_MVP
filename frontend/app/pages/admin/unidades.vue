<script setup lang="ts">
import type { Unidade } from '~/types'
import { formatarTelefone } from '~/utils/masks'

definePageMeta({ layout: 'admin' })

const unidadesStore = useUnidadesStore()
const openNav = inject<() => void>('openNav', () => {})

const busca = ref('')
const showFormModal = ref(false)
const editingUnidade = ref<Unidade | null>(null)
const confirmDeleteId = ref<number | null>(null)

const listaFiltrada = computed(() => {
  const lista = unidadesStore.unidades
  const termo = busca.value.trim().toLowerCase()
  if (!termo) return lista
  const termoDigitos = termo.replace(/\D/g, '')
  return lista.filter(u =>
    u.nome.toLowerCase().includes(termo)
    || u.endereco.toLowerCase().includes(termo)
    || (termoDigitos.length > 0 && u.telefone.replace(/\D/g, '').includes(termoDigitos))
    || u.codigo_spdata_centro_custo.toLowerCase().includes(termo)
    || u.codigo_spdata_agenda.toLowerCase().includes(termo)
  )
})

onMounted(() => {
  unidadesStore.fetchAll()
})

function abrirNovo() {
  editingUnidade.value = null
  showFormModal.value = true
}

function editar(u: Unidade) {
  editingUnidade.value = u
  showFormModal.value = true
}

function confirmarExclusao(id: number) {
  confirmDeleteId.value = id
}

async function executarExclusao() {
  if (confirmDeleteId.value === null) return
  const res = await unidadesStore.excluir(confirmDeleteId.value)
  if (res.success) {
    useToast().add({ title: res.message, color: 'success' })
  } else {
    useToast().add({ title: res.message, color: 'error' })
  }
  confirmDeleteId.value = null
}

function onSaved() {
  unidadesStore.fetchAll()
}
</script>

<template>
  <div>
    <UHeader
      title="Unidades"
      toggle-side="left"
    >
      <template #toggle>
        <UButton
          icon="i-lucide-panel-left"
          color="neutral"
          variant="ghost"
          class="min-h-11 min-w-11 lg:hidden"
          aria-label="Abrir menu"
          @click="openNav()"
        />
      </template>
      <template #right>
        <div class="flex flex-wrap items-center justify-end gap-2">
          <UButton
            icon="i-lucide-plus"
            label="Nova Unidade"
            :ui="{ label: 'hidden sm:inline' }"
            aria-label="Nova Unidade"
            @click="abrirNovo"
          />
          <UColorModeButton />
        </div>
      </template>
    </UHeader>

    <div class="min-h-screen space-y-6 bg-neutral-100 p-4 dark:bg-neutral-950 sm:p-6">
      <UInput
        v-model="busca"
        icon="i-lucide-search"
        placeholder="Buscar por nome, endereco, telefone..."
        class="w-full"
        aria-label="Buscar unidades"
      />

      <div
        v-if="unidadesStore.loading"
        class="flex justify-center py-12"
      >
        <UIcon
          name="i-lucide-loader-circle"
          class="size-8 animate-spin text-muted"
        />
      </div>

      <div
        v-else-if="unidadesStore.error"
        class="flex flex-col items-center justify-center py-16 gap-3 text-center w-full"
      >
        <UAlert
          :title="`Erro inesperado: (${unidadesStore.error})`"
          color="error"
          variant="subtle"
          icon="i-lucide-circle-alert"
          class="w-full max-w-sm"
        />
        <UButton
          label="Tentar novamente"
          color="neutral"
          variant="outline"
          @click="unidadesStore.fetchAll()"
        />
      </div>

      <div
        v-else-if="listaFiltrada.length === 0"
        class="flex flex-col items-center py-16 gap-3 text-center"
      >
        <UIcon
          name="i-lucide-building"
          class="size-12 text-muted"
        />
        <p class="text-lg font-medium text-muted">
          Nenhuma unidade encontrada
        </p>
        <p class="text-sm text-muted">
          {{ busca ? 'Tente buscar com outro termo.' : 'Clique em "Nova Unidade" para adicionar.' }}
        </p>
      </div>

      <UCard
        v-else
        class="w-full"
      >
        <div class="flex flex-col">
          <UPageCard
            v-for="unidade in listaFiltrada"
            :key="unidade.id"
            variant="ghost"
            class="border-b border-muted rounded-none"
            :ui="{ container: 'px-4 sm:p-1 pb-3 sm:px-4' }"
          >
            <div class="grid min-w-0 grid-cols-1 gap-x-4 gap-y-3 sm:grid-cols-2 lg:grid-cols-12 lg:items-center">
              <div class="lg:col-span-1">
                <p class="text-sm font-bold text-muted">
                  ID
                </p>
                <p class="font-mono text-sm">
                  {{ unidade.id }}
                </p>
              </div>

              <div class="lg:col-span-3">
                <p class="text-sm font-bold text-muted">
                  Nome
                </p>
                <p class="wrap-break-word font-medium">
                  {{ unidade.nome }}
                </p>
                <p class="wrap-break-word text-xs text-muted">
                  {{ unidade.endereco }}
                </p>
              </div>

              <div class="lg:col-span-2">
                <p class="text-sm font-bold text-muted">
                  Centro de Custo
                </p>
                <p class="wrap-break-word text-sm">
                  {{ unidade.codigo_spdata_centro_custo || '-' }}
                </p>
              </div>

              <div class="lg:col-span-2">
                <p class="text-sm font-bold text-muted">
                  Agenda SPDATA
                </p>
                <p class="wrap-break-word text-sm">
                  {{ unidade.codigo_spdata_agenda || '-' }}
                </p>
              </div>

              <div class="lg:col-span-2">
                <p class="text-sm font-bold text-muted">
                  Telefone
                </p>
                <span class="whitespace-nowrap text-sm">
                  {{ unidade.telefone ? formatarTelefone(unidade.telefone) : '-' }}
                </span>
              </div>

              <div class="lg:col-span-1">
                <p class="text-sm font-bold text-muted">
                  Status
                </p>
                <UBadge
                  :label="unidade.ativa ? 'Ativa' : 'Inativa'"
                  :color="unidade.ativa ? 'success' : 'neutral'"
                  variant="subtle"
                  size="sm"
                />
              </div>

              <div class="sm:col-span-2 lg:col-span-1">
                <p class="text-sm font-bold text-muted">
                  Ações
                </p>
                <div class="flex items-center gap-1">
                  <UButton
                    icon="i-lucide-pencil"
                    color="neutral"
                    variant="ghost"
                    size="sm"
                    class="min-h-11 min-w-11 sm:min-h-8 sm:min-w-8"
                    :aria-label="`Editar ${unidade.nome}`"
                    title="Editar unidade"
                    @click="editar(unidade)"
                  />
                  <UButton
                    icon="i-lucide-trash-2"
                    color="error"
                    variant="ghost"
                    size="sm"
                    class="min-h-11 min-w-11 sm:min-h-8 sm:min-w-8"
                    :aria-label="`Inativar ${unidade.nome}`"
                    title="Inativar unidade"
                    :disabled="unidade.ativa === false"
                    @click="confirmarExclusao(unidade.id)"
                  />
                </div>
              </div>
            </div>
          </UPageCard>
        </div>
      </UCard>
    </div>

    <UnidadeFormModal
      v-model:open="showFormModal"
      :unidade="editingUnidade"
      @saved="onSaved"
    />

    <ModalConfirmacao
      :abrir="confirmDeleteId !== null"
      titulo="Inativar Unidade?"
      descricao="Tem certeza que deseja inativar esta unidade? Ela permanecera no historico do sistema."
      texto-confirma="Inativar"
      @fechar="confirmDeleteId = null"
      @confirmar="executarExclusao"
    />
  </div>
</template>
