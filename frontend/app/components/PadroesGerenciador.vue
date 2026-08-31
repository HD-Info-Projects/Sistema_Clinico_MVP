<script setup lang="ts">
import type { PadraoReceita, PadraoExame, PadraoAnamnese, PadraoOrientacaoExame } from '~/types'

const props = defineProps<{
  /** Medico alvo quando um admin gerencia os padroes de outro usuario */
  medicoId?: number | null
}>()

const padroesStore = usePadroesStore()
const padroesAnamneseStore = usePadroesAnamneseStore()
const padroesOrientacoesStore = usePadroesOrientacoesStore()
const toast = useToast()

onMounted(() => {
  const medicoId = props.medicoId ?? undefined
  padroesStore.fetchAll(medicoId)
  padroesAnamneseStore.fetchAll(medicoId)
  padroesOrientacoesStore.fetchAll(medicoId)
})

type ActiveTab = 'receitas' | 'exames' | 'anamnese' | 'orientacoes'

const activeTab = ref<ActiveTab | null>(null)

const showReceitaModal = ref(false)
const showExameModal = ref(false)
const showAnamneseModal = ref(false)
const showOrientacaoModal = ref(false)

const editingReceita = ref<PadraoReceita | null>(null)
const editingExame = ref<PadraoExame | null>(null)
const editingAnamnese = ref<PadraoAnamnese | null>(null)
const editingOrientacao = ref<PadraoOrientacaoExame | null>(null)

const confirmDeleteId = ref<string | null>(null)
const confirmDeleteTipo = ref<'receita' | 'exame' | 'anamnese' | 'orientacao' | null>(null)

function abrirNovaReceita() {
  editingReceita.value = null
  showReceitaModal.value = true
}

function abrirNovaExame() {
  editingExame.value = null
  showExameModal.value = true
}

function abrirNovaAnamnese() {
  editingAnamnese.value = null
  showAnamneseModal.value = true
}

function abrirNovaOrientacao() {
  editingOrientacao.value = null
  showOrientacaoModal.value = true
}

function editarReceita(p: PadraoReceita) {
  editingReceita.value = p
  showReceitaModal.value = true
}

function editarExame(p: PadraoExame) {
  editingExame.value = p
  showExameModal.value = true
}

function editarAnamnese(p: PadraoAnamnese) {
  editingAnamnese.value = p
  showAnamneseModal.value = true
}

function editarOrientacao(p: PadraoOrientacaoExame) {
  editingOrientacao.value = p
  showOrientacaoModal.value = true
}

function confirmarDeletar(p: PadraoReceita | PadraoExame | PadraoAnamnese | PadraoOrientacaoExame, tipo: 'receita' | 'exame' | 'anamnese' | 'orientacao') {
  confirmDeleteId.value = p.id
  confirmDeleteTipo.value = tipo
}

async function executarDeletar() {
  if (confirmDeleteId.value !== null) {
    try {
      const medicoId = props.medicoId ?? undefined
      if (confirmDeleteTipo.value === 'anamnese') {
        await padroesAnamneseStore.deletar(confirmDeleteId.value, medicoId)
      } else if (confirmDeleteTipo.value === 'orientacao') {
        await padroesOrientacoesStore.deletar(confirmDeleteId.value, medicoId)
      } else {
        await padroesStore.deletar(confirmDeleteId.value, medicoId)
      }
    } catch {
      toast.add({
        title: 'Erro ao Deletar',
        description: 'Não foi possível deletar o padrão',
        color: 'error',
        icon: 'lucide:octagon-x'
      })
    } finally {
      confirmDeleteId.value = null
      confirmDeleteTipo.value = null
    }
  }
}

function gerenciarReceita() {
  activeTab.value = 'receitas'
}

function gerenciarExame() {
  activeTab.value = 'exames'
}

function gerenciarAnamnese() {
  activeTab.value = 'anamnese'
}

function gerenciarOrientacao() {
  activeTab.value = 'orientacoes'
}

function activeTabIcon(tab: ActiveTab) {
  if (tab === 'receitas') return 'i-lucide-pill'
  if (tab === 'exames') return 'i-lucide-flask-conical'
  if (tab === 'anamnese') return 'i-lucide-notebook-text'
  return 'i-lucide-message-square-text'
}

function activeTabTitulo(tab: ActiveTab) {
  if (tab === 'receitas') return 'Receitas Médicas'
  if (tab === 'exames') return 'Pedidos de Exames'
  if (tab === 'anamnese') return 'Anamnese'
  return 'Orientações de Exames'
}

function activeTabEmpty(): boolean {
  if (activeTab.value === 'receitas') return padroesStore.receitas.length === 0
  if (activeTab.value === 'exames') return padroesStore.exames.length === 0
  if (activeTab.value === 'anamnese') return padroesAnamneseStore.padroes.length === 0
  if (activeTab.value === 'orientacoes') return padroesOrientacoesStore.padroes.length === 0
  return true
}
</script>

<template>
  <div class="space-y-6">
    <div class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-6">
      <UCard>
        <template #title>
          <div class="flex items-center gap-2">
            <UIcon
              name="i-lucide-pill"
              class="text-primary"
            />
            <p class="min-w-0 break-words font-semibold">
              Receitas Médicas
            </p>
          </div>
        </template>

        <template #description>
          <p class="break-words text-sm text-muted">
            Modelos de receita com listas de medicamentos pré-definidos.
          </p>
        </template>

        <div class="flex flex-col gap-2 sm:flex-row">
          <UButton
            icon="i-lucide-plus"
            label="Novo Modelo"
            size="sm"
            class="w-full justify-center sm:w-auto"
            @click="abrirNovaReceita"
          />
          <UButton
            label="Gerenciar"
            color="neutral"
            size="sm"
            class="w-full justify-center sm:w-auto"
            @click="gerenciarReceita"
          />
        </div>
      </UCard>

      <UCard>
        <template #title>
          <div class="flex items-center gap-2">
            <UIcon
              name="i-lucide-flask-conical"
              class="text-primary"
            />
            <p class="min-w-0 break-words font-semibold">
              Pedidos de Exames
            </p>
          </div>
        </template>

        <template #description>
          <p class="break-words text-sm text-muted">
            Conjuntos de exames para solicitação. No atendimento você seleciona quais entrarão no pedido.
          </p>
        </template>

        <div class="flex flex-col gap-2 sm:flex-row">
          <UButton
            icon="i-lucide-plus"
            label="Novo Modelo"
            size="sm"
            class="w-full justify-center sm:w-auto"
            @click="abrirNovaExame"
          />
          <UButton
            label="Gerenciar"
            color="neutral"
            size="sm"
            class="w-full justify-center sm:w-auto"
            @click="gerenciarExame"
          />
        </div>
      </UCard>

      <UCard>
        <template #title>
          <div class="flex items-center gap-2">
            <UIcon
              name="i-lucide-notebook-text"
              class="text-primary"
            />
            <p class="min-w-0 break-words font-semibold">
              Anamnese
            </p>
          </div>
        </template>

        <template #description>
          <p class="break-words text-sm text-muted">
            Modelos de anamnese com texto pré-formatado. No atendimento você insere o padrão no editor.
          </p>
        </template>

        <div class="flex flex-col gap-2 sm:flex-row">
          <UButton
            icon="i-lucide-plus"
            label="Novo Modelo"
            size="sm"
            class="w-full justify-center sm:w-auto"
            @click="abrirNovaAnamnese"
          />
          <UButton
            label="Gerenciar"
            color="neutral"
            size="sm"
            class="w-full justify-center sm:w-auto"
            @click="gerenciarAnamnese"
          />
        </div>
      </UCard>

      <UCard>
        <template #title>
          <div class="flex items-center gap-2">
            <UIcon
              name="i-lucide-message-square-text"
              class="text-primary"
            />
            <p class="min-w-0 break-words font-semibold">
              Orientações de Exames
            </p>
          </div>
        </template>

        <template #description>
          <p class="break-words text-sm text-muted">
            Modelos de orientações impressas como folha extra junto da solicitação de exames.
          </p>
        </template>

        <div class="flex flex-col gap-2 sm:flex-row">
          <UButton
            icon="i-lucide-plus"
            label="Novo Modelo"
            size="sm"
            class="w-full justify-center sm:w-auto"
            @click="abrirNovaOrientacao"
          />
          <UButton
            label="Gerenciar"
            color="neutral"
            size="sm"
            class="w-full justify-center sm:w-auto"
            @click="gerenciarOrientacao"
          />
        </div>
      </UCard>
    </div>

    <UCard v-if="activeTab">
      <template #title>
        <div class="flex min-w-0 items-center gap-2">
          <UIcon
            :name="activeTabIcon(activeTab)"
            class="text-primary"
          />
          <p class="min-w-0 break-words font-semibold">
            Modelos de {{ activeTabTitulo(activeTab) }}
          </p>
        </div>
      </template>

      <div class="space-y-2">
        <template v-if="activeTab === 'receitas'">
          <div
            v-for="p in padroesStore.receitas"
            :key="p.id"
            class="flex min-w-0 flex-col gap-2 rounded-lg border border-muted p-3 hover:bg-muted/50 sm:flex-row sm:items-center sm:justify-between"
          >
            <div class="min-w-0">
              <p class="break-words font-medium">
                {{ p.nome }}
              </p>
              <p class="break-words text-xs text-muted">
                {{ p.medicamentos.length }} medicamento{{ p.medicamentos.length !== 1 ? 's' : '' }}
                &middot; {{ new Date(p.updatedAt).toLocaleDateString('pt-BR') }}
              </p>
            </div>
            <div class="flex shrink-0 self-end gap-1 sm:self-auto">
              <UButton
                icon="i-lucide-pencil"
                color="neutral"
                variant="ghost"
                size="sm"
                class="min-h-11 min-w-11 sm:min-h-8 sm:min-w-8"
                aria-label="Editar padrão de receita"
                @click="editarReceita(p)"
              />
              <UButton
                icon="i-lucide-trash-2"
                color="error"
                variant="ghost"
                size="sm"
                class="min-h-11 min-w-11 sm:min-h-8 sm:min-w-8"
                aria-label="Excluir padrão de receita"
                @click="confirmarDeletar(p, 'receita')"
              />
            </div>
          </div>
        </template>

        <template v-else-if="activeTab === 'exames'">
          <div
            v-for="p in padroesStore.exames"
            :key="p.id"
            class="flex min-w-0 flex-col gap-2 rounded-lg border border-muted p-3 hover:bg-muted/50 sm:flex-row sm:items-center sm:justify-between"
          >
            <div class="min-w-0">
              <p class="break-words font-medium">
                {{ p.nome }}
              </p>
              <p class="break-words text-xs text-muted">
                {{ p.exames.length }} exame{{ p.exames.length !== 1 ? 's' : '' }}
                &middot; {{ new Date(p.updatedAt).toLocaleDateString('pt-BR') }}
              </p>
            </div>
            <div class="flex shrink-0 self-end gap-1 sm:self-auto">
              <UButton
                icon="i-lucide-pencil"
                color="neutral"
                variant="ghost"
                size="sm"
                class="min-h-11 min-w-11 sm:min-h-8 sm:min-w-8"
                aria-label="Editar padrão de exames"
                @click="editarExame(p)"
              />
              <UButton
                icon="i-lucide-trash-2"
                color="error"
                variant="ghost"
                size="sm"
                class="min-h-11 min-w-11 sm:min-h-8 sm:min-w-8"
                aria-label="Excluir padrão de exames"
                @click="confirmarDeletar(p, 'exame')"
              />
            </div>
          </div>
        </template>

        <template v-else-if="activeTab === 'anamnese'">
          <div
            v-for="p in padroesAnamneseStore.padroes"
            :key="p.id"
            class="flex min-w-0 flex-col gap-2 rounded-lg border border-muted p-3 hover:bg-muted/50 sm:flex-row sm:items-center sm:justify-between"
          >
            <div class="min-w-0">
              <p class="break-words font-medium">
                {{ p.nome }}
              </p>
              <p class="text-xs text-muted">
                {{ new Date(p.updatedAt).toLocaleDateString('pt-BR') }}
              </p>
            </div>
            <div class="flex shrink-0 self-end gap-1 sm:self-auto">
              <UButton
                icon="i-lucide-pencil"
                color="neutral"
                variant="ghost"
                size="sm"
                class="min-h-11 min-w-11 sm:min-h-8 sm:min-w-8"
                aria-label="Editar padrão de anamnese"
                @click="editarAnamnese(p)"
              />
              <UButton
                icon="i-lucide-trash-2"
                color="error"
                variant="ghost"
                size="sm"
                class="min-h-11 min-w-11 sm:min-h-8 sm:min-w-8"
                aria-label="Excluir padrão de anamnese"
                @click="confirmarDeletar(p, 'anamnese')"
              />
            </div>
          </div>
        </template>

        <template v-else-if="activeTab === 'orientacoes'">
          <div
            v-for="p in padroesOrientacoesStore.padroes"
            :key="p.id"
            class="flex min-w-0 flex-col gap-2 rounded-lg border border-muted p-3 hover:bg-muted/50 sm:flex-row sm:items-center sm:justify-between"
          >
            <div class="min-w-0">
              <p class="break-words font-medium">
                {{ p.nome }}
              </p>
              <p class="text-xs text-muted">
                {{ new Date(p.updatedAt).toLocaleDateString('pt-BR') }}
              </p>
            </div>
            <div class="flex shrink-0 self-end gap-1 sm:self-auto">
              <UButton
                icon="i-lucide-pencil"
                color="neutral"
                variant="ghost"
                size="sm"
                class="min-h-11 min-w-11 sm:min-h-8 sm:min-w-8"
                aria-label="Editar padrão de orientação"
                @click="editarOrientacao(p)"
              />
              <UButton
                icon="i-lucide-trash-2"
                color="error"
                variant="ghost"
                size="sm"
                class="min-h-11 min-w-11 sm:min-h-8 sm:min-w-8"
                aria-label="Excluir padrão de orientação"
                @click="confirmarDeletar(p, 'orientacao')"
              />
            </div>
          </div>
        </template>

        <p
          v-if="activeTabEmpty()"
          class="text-sm text-muted italic py-4 text-center"
        >
          Nenhum modelo cadastrado.
        </p>
      </div>
    </UCard>

    <PadraoReceitaModal
      v-model:open="showReceitaModal"
      :padrao="editingReceita"
      :medico-id="medicoId"
    />

    <PadraoExameModal
      v-model:open="showExameModal"
      :padrao="editingExame"
      :medico-id="medicoId"
    />

    <PadraoAnamneseModal
      v-model:open="showAnamneseModal"
      :padrao="editingAnamnese"
      :medico-id="medicoId"
    />

    <PadraoOrientacaoModal
      v-model:open="showOrientacaoModal"
      :padrao="editingOrientacao"
      :medico-id="medicoId"
    />

    <ModalConfirmacao
      :abrir="confirmDeleteId !== null"
      titulo="Deletar Padrão?"
      descricao="Tem certeza que deseja deletar este padrão?"
      texto-confirma="Deletar"
      @fechar="confirmDeleteId = null"
      @confirmar="executarDeletar"
    />
  </div>
</template>
