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

const colunas = [
  { accessorKey: 'id', header: 'ID' },
  { accessorKey: 'nome', header: 'Nome' },
  { accessorKey: 'codigo_spdata_centro_custo', header: 'Centro de Custo' },
  { accessorKey: 'codigo_spdata_agenda', header: 'Agenda' },
  { accessorKey: 'telefone', header: 'Telefone' },
  { accessorKey: 'ativa', header: 'Status' },
  { id: 'acoes', header: 'Acoes' }
]

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
        <div class="w-full overflow-x-auto">
          <UTable
            :columns="colunas"
            :data="listaFiltrada"
            class="min-w-[56rem]"
          >
            <template #nome-cell="{ row }">
              <div class="min-w-0 max-w-xs">
                <p class="break-words font-medium">
                  {{ row.original.nome }}
                </p>
                <p class="break-words text-xs text-muted">
                  {{ row.original.endereco }}
                </p>
              </div>
            </template>

            <template #telefone-cell="{ row }">
              <span class="text-sm whitespace-nowrap">
                {{ row.original.telefone ? formatarTelefone(row.original.telefone) : '-' }}
              </span>
            </template>

            <template #ativa-cell="{ row }">
              <UBadge
                :label="row.original.ativa ? 'Ativa' : 'Inativa'"
                :color="row.original.ativa ? 'success' : 'neutral'"
                variant="subtle"
                size="sm"
              />
            </template>

            <template #acoes-cell="{ row }">
              <div class="flex items-center gap-1">
                <UButton
                  icon="i-lucide-pencil"
                  color="neutral"
                  variant="ghost"
                  size="sm"
                  class="min-h-11 min-w-11 sm:min-h-8 sm:min-w-8"
                  aria-label="Editar unidade"
                  @click="editar(row.original)"
                />
                <UButton
                  icon="i-lucide-trash-2"
                  color="error"
                  variant="ghost"
                  size="sm"
                  class="min-h-11 min-w-11 sm:min-h-8 sm:min-w-8"
                  aria-label="Inativar unidade"
                  :disabled="row.original.ativa === false"
                  @click="confirmarExclusao(row.original.id)"
                />
              </div>
            </template>
          </UTable>
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
