<script setup lang="ts">
import type { Usuario, RoleUsuario } from '~/types'
import { formatarCpfCnpj } from '~/utils/masks'

const props = defineProps<{
  role: RoleUsuario
  titulo: string
  placeholderBusca: string
}>()

const usuariosStore = useUsuariosStore()
const openNav = inject<() => void>('openNav', () => {})

const busca = ref('')
const showFormModal = ref(false)
const editingUsuario = ref<Usuario | null>(null)
const confirmDeleteId = ref<number | null>(null)

let buscaTimer: ReturnType<typeof setTimeout> | null = null

const listaFiltrada = computed(() => {
  const lista = usuariosStore.porRole(props.role)
  const termo = busca.value.trim().toLowerCase()
  if (!termo) return lista
  const termoDigitos = termo.replace(/\D/g, '')
  return lista.filter(u =>
    u.nome_completo.toLowerCase().includes(termo)
    || u.email.toLowerCase().includes(termo)
    || (termoDigitos.length > 0 && u.cnpj_cpf.includes(termoDigitos))
    || (u.medico?.crm?.toLowerCase().includes(termo))
    || (u.medico?.especialidade?.toLowerCase().includes(termo))
  )
})

onMounted(() => {
  usuariosStore.fetchAll(props.role)
})

watch(busca, () => {
  if (buscaTimer) clearTimeout(buscaTimer)
  buscaTimer = setTimeout(() => {
    // debounce para futuras expansoes
  }, 300)
})

function abrirNovo() {
  editingUsuario.value = null
  showFormModal.value = true
}

function editar(u: Usuario) {
  editingUsuario.value = u
  showFormModal.value = true
}

function confirmarExclusao(id: number) {
  confirmDeleteId.value = id
}

async function executarExclusao() {
  if (confirmDeleteId.value === null) return
  const res = await usuariosStore.excluir(confirmDeleteId.value)
  if (res.success) {
    useToast().add({ title: res.message, color: 'success' })
  } else {
    useToast().add({ title: res.message, color: 'error' })
  }
  confirmDeleteId.value = null
}

function onSaved() {
  usuariosStore.fetchAll(props.role)
}
</script>

<template>
  <div>
    <UHeader
      :title="titulo"
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
            :label="`Novo ${titulo.replace('s', '')}`"
            :ui="{ label: 'hidden sm:inline' }"
            :aria-label="`Novo ${titulo.replace('s', '')}`"
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
        :placeholder="placeholderBusca"
        class="w-full"
        :aria-label="`Buscar ${titulo.toLowerCase()}`"
      />

      <div
        v-if="usuariosStore.loading"
        class="flex justify-center py-12"
      >
        <UIcon
          name="i-lucide-loader-circle"
          class="size-8 animate-spin text-muted"
        />
      </div>

      <div
        v-else-if="usuariosStore.error"
        class="flex flex-col items-center justify-center py-16 gap-3 text-center w-full"
      >
        <UAlert
          :title="`Erro inesperado: (${usuariosStore.error})`"
          color="error"
          variant="subtle"
          icon="i-lucide-circle-alert"
          class="w-full max-w-sm"
        />
        <UButton
          label="Tentar novamente"
          color="neutral"
          variant="outline"
          @click="usuariosStore.fetchAll(role)"
        />
      </div>

      <div
        v-else-if="listaFiltrada.length === 0"
        class="flex flex-col items-center py-16 gap-3 text-center"
      >
        <UIcon
          name="i-lucide-users"
          class="size-12 text-muted"
        />
        <p class="text-lg font-medium text-muted">
          Nenhum {{ titulo.toLowerCase() }} encontrado
        </p>
        <p class="text-sm text-muted">
          {{ busca ? 'Tente buscar com outro termo.' : 'Clique em "Novo" para adicionar.' }}
        </p>
      </div>

      <UCard
        v-else
        class="w-full"
      >
        <div class="flex flex-col">
          <UPageCard
            v-for="usuario in listaFiltrada"
            :key="usuario.id"
            variant="ghost"
            class="border-b border-muted rounded-none"
            :ui="{ container: 'px-4 sm:p-1 pb-3 sm:px-4' }"
          >
            <div class="grid min-w-0 grid-cols-1 gap-x-4 gap-y-3 sm:grid-cols-2 lg:grid-cols-12 lg:items-center">
              <div :class="role === 'medico' ? 'lg:col-span-3' : 'lg:col-span-4'">
                <p class="text-sm font-bold text-muted">
                  Nome
                </p>
                <div class="flex min-w-0 items-center gap-3">
                  <UAvatar
                    :alt="usuario.nome_completo"
                    color="primary"
                    size="sm"
                  />
                  <div class="min-w-0">
                    <p class="wrap-break-word font-medium">
                      {{ usuario.nome_completo }}
                    </p>
                    <p class="text-xs text-muted">
                      {{ formatarCpfCnpj(usuario.cnpj_cpf) }}
                    </p>
                  </div>
                </div>
              </div>

              <div
                v-if="role === 'medico'"
                class="lg:col-span-1"
              >
                <p class="text-sm font-bold text-muted">
                  CRM
                </p>
                <span class="font-mono text-sm">
                  {{ usuario.medico?.crm || usuario.medico?.crm_atendimento_spdata || '-' }}
                </span>
              </div>

              <div
                v-if="role === 'medico'"
                class="lg:col-span-2"
              >
                <p class="text-sm font-bold text-muted">
                  Especialidade
                </p>
                <UBadge
                  v-if="usuario.medico?.especialidade"
                  :label="usuario.medico.especialidade"
                  color="neutral"
                  variant="subtle"
                  size="sm"
                />
                <span
                  v-else
                  class="text-sm text-muted"
                >-</span>
              </div>

              <div :class="role === 'medico' ? 'lg:col-span-2' : 'lg:col-span-4'">
                <p class="text-sm font-bold text-muted">
                  Email
                </p>
                <p class="break-all text-sm">
                  {{ usuario.email }}
                </p>
              </div>

              <div :class="role === 'medico' ? 'lg:col-span-1' : 'lg:col-span-2'">
                <p class="text-sm font-bold text-muted">
                  Status
                </p>
                <UBadge
                  :label="usuario.ativo ? 'Ativo' : 'Inativo'"
                  :color="usuario.ativo ? 'success' : 'neutral'"
                  variant="subtle"
                  size="sm"
                />
              </div>

              <div :class="role === 'medico' ? 'sm:col-span-2 lg:col-span-3' : 'sm:col-span-2 lg:col-span-2'">
                <p class="text-sm font-bold text-muted">
                  Ações
                </p>
                <div class="flex items-center gap-1">
                  <UButton
                    v-if="role === 'medico'"
                    icon="i-lucide-notebook-pen"
                    color="neutral"
                    variant="ghost"
                    size="sm"
                    class="min-h-11 min-w-11 sm:min-h-8 sm:min-w-8"
                    :aria-label="`Padrões de ${usuario.nome_completo}`"
                    title="Padrões"
                    @click="void(navigateTo(`/admin/padroes-medico/${usuario.id}`))"
                  />
                  <UButton
                    icon="i-lucide-pencil"
                    color="neutral"
                    variant="ghost"
                    size="sm"
                    class="min-h-11 min-w-11 sm:min-h-8 sm:min-w-8"
                    :aria-label="`Editar ${usuario.nome_completo}`"
                    title="Editar usuário"
                    @click="editar(usuario)"
                  />
                  <UButton
                    icon="i-lucide-trash-2"
                    color="error"
                    variant="ghost"
                    size="sm"
                    class="min-h-11 min-w-11 sm:min-h-8 sm:min-w-8"
                    :aria-label="`Inativar ${usuario.nome_completo}`"
                    title="Inativar usuário"
                    :disabled="usuario.ativo === false"
                    @click="confirmarExclusao(usuario.id)"
                  />
                </div>
              </div>
            </div>
          </UPageCard>
        </div>
      </UCard>
    </div>

    <UsuarioFormModal
      v-model:open="showFormModal"
      :usuario="editingUsuario"
      :role="role"
      @saved="onSaved"
    />

    <ModalConfirmacao
      :abrir="confirmDeleteId !== null"
      titulo="Inativar Usuario?"
      descricao="Tem certeza que deseja inativar este usuario? Ele nao podera acessar o sistema."
      texto-confirma="Inativar"
      @fechar="confirmDeleteId = null"
      @confirmar="executarExclusao"
    />
  </div>
</template>
