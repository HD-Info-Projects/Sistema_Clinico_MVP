<script setup lang="ts">
import type { Usuario } from '~/types'
import { useUnidadesStore } from '~/features/unidades/stores/unidadesStore'

definePageMeta({ layout: 'admin' })

const auth = useAuthStore()
const usuariosStore = useUsuariosStore()
const unidadesStore = useUnidadesStore()
const openNav = inject<() => void>('openNav', () => {})
const showFormModal = ref(false)
const editingUsuario = ref<Usuario | null>(null)
const confirmDeleteId = ref<number | null>(null)
const confirmUnlockId = ref<number | null>(null)

const userName = computed(() => auth.user?.nome || 'Administrador')

const totalMedicos = computed(() => usuariosStore.porRole('medico').filter(u => u.ativo !== false).length)
const totalRecepcao = computed(() => usuariosStore.porRole('recepcao').filter(u => u.ativo !== false).length)
const totalAdmins = computed(() => usuariosStore.porRole('admin').filter(u => u.ativo !== false).length)
const totalUnidades = computed(() => unidadesStore.unidades.filter(u => u.ativa).length)
// const totalUsuarios = computed(() => totalMedicos.value + totalRecepcao.value + totalAdmins.value)

const ultimosUsuarios = computed(() => {
  return [...usuariosStore.usuarios]
    .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
    .slice(0, 10)
})

onMounted(() => {
  usuariosStore.fetchAll()
  unidadesStore.fetchAll()
})

function corRole(role: string) {
  switch (role) {
    case 'admin': return 'error'
    case 'medico': return 'primary'
    case 'recepcao': return 'success'
    default: return 'neutral'
  }
}

function rotuloRole(role: string) {
  switch (role) {
    case 'admin': return 'Administrador'
    case 'medico': return 'Medico'
    case 'recepcao': return 'Recepcionista'
    default: return role
  }
}

function formatarData(data: string) {
  return new Date(data).toLocaleDateString('pt-BR')
}

function editar(usuario: Usuario) {
  editingUsuario.value = usuario
  showFormModal.value = true
}

async function executarExclusao() {
  if (confirmDeleteId.value === null) return

  const res = await usuariosStore.excluir(confirmDeleteId.value)
  useToast().add({
    title: res.message,
    color: res.success ? 'success' : 'error'
  })
  confirmDeleteId.value = null
}

async function executarDesbloqueio() {
  if (confirmUnlockId.value === null) return

  const res = await usuariosStore.desbloquear(confirmUnlockId.value)
  useToast().add({
    title: res.message,
    color: res.success ? 'success' : 'error'
  })
  confirmUnlockId.value = null
}

function onSaved() {
  usuariosStore.fetchAll()
}
</script>

<template>
  <div>
    <UHeader
      title="Dashboard Administrativo"
      toggle-side="left"
    >
      <template #toggle>
        <UButton
          icon="i-lucide-menu"
          color="neutral"
          variant="ghost"
          class="min-h-11 min-w-11 lg:hidden"
          aria-label="Abrir menu"
          @click="openNav()"
        />
      </template>
      <template #right>
        <div class="flex min-w-0 items-center justify-end gap-2">
          <UBadge
            :label="userName"
            color="neutral"
            variant="soft"
            class="hidden max-w-48 truncate sm:inline-flex"
          />
          <UColorModeButton />
        </div>
      </template>
    </UHeader>

    <div class="min-h-screen space-y-6 bg-muted p-4 sm:p-6">
      <div class="min-w-0">
        <p class="wrap-break-word text-2xl font-semibold sm:text-3xl">
          Bem-vindo, {{ userName }}
        </p>
        <p class="text-base text-muted mt-1">
          Gerencie os usuarios do sistema
        </p>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-6">
        <CardInformativo
          titulo="Médicos"
          :valor="totalMedicos"
          cor="primary"
          icone="i-lucide-stethoscope"
        >
          <div class="flex justify-end">
            <UButton
              label="Gerenciar"
              color="primary"
              class="mt-3"
              to="/admin/medicos"
            />
          </div>
        </CardInformativo>

        <CardInformativo
          titulo="Recepcionistas"
          :valor="totalRecepcao"
          cor="success"
          icone="i-lucide-user-check"
        >
          <div class="flex justify-end">
            <UButton
              label="Gerenciar"
              color="primary"
              class="mt-3"
              to="/admin/recepcao"
            />
          </div>
        </CardInformativo>

        <CardInformativo
          titulo="Administradores"
          :valor="totalAdmins"
          cor="error"
          icone="i-lucide-shield"
        >
          <div class="flex justify-end">
            <UButton
              label="Gerenciar"
              color="primary"
              class="mt-3"
              to="/admin/admins"
            />
          </div>
        </CardInformativo>

        <CardInformativo
          titulo="Unidades"
          :valor="totalUnidades"
          cor="tertiary"
          icone="i-lucide-building"
        >
          <div class="flex justify-end">
            <UButton
              label="Gerenciar"
              color="primary"
              class="mt-3"
              to="/admin/unidades"
            />
          </div>
        </CardInformativo>
      </div>

      <UCard class="w-full">
        <template #title>
          <div class="flex items-center gap-2">
            <UIcon
              name="i-lucide-clock"
              class="text-primary"
            />
            <p class="font-semibold">
              Ultimos Cadastros
            </p>
          </div>
        </template>

        <div
          v-if="usuariosStore.loading"
          class="flex justify-center py-8"
        >
          <UIcon
            name="i-lucide-loader-circle"
            class="size-8 animate-spin text-muted"
          />
        </div>

        <div
          v-else-if="ultimosUsuarios.length === 0"
          class="flex flex-col items-center py-8 gap-2 text-center"
        >
          <UIcon
            name="i-lucide-users"
            class="size-10 text-muted"
          />
          <p class="text-muted">
            Nenhum usuario cadastrado ainda
          </p>
        </div>

        <div
          v-else
          class="flex flex-col"
        >
          <UPageCard
            v-for="usuario in ultimosUsuarios"
            :key="usuario.id"
            variant="ghost"
            class="border-b border-muted rounded-none"
            :ui="{ container: 'px-4 sm:p-1 pb-3 sm:px-4' }"
          >
            <div class="grid min-w-0 grid-cols-1 gap-x-4 gap-y-3 sm:grid-cols-2 lg:grid-cols-12 lg:items-center">
              <div class="lg:col-span-3">
                <p class="text-sm font-bold text-muted">
                  Nome
                </p>
                <div class="flex min-w-0 items-center gap-3">
                  <UAvatar
                    :alt="usuario.nome_completo"
                    color="primary"
                    size="sm"
                  />
                  <p class="min-w-0 wrap-break-word font-medium">
                    {{ usuario.nome_completo }}
                  </p>
                </div>
              </div>

              <div class="lg:col-span-2">
                <p class="text-sm font-bold text-muted">
                  Perfil
                </p>
                <UBadge
                  :label="rotuloRole(usuario.role)"
                  :color="corRole(usuario.role)"
                  variant="subtle"
                />
              </div>

              <div class="lg:col-span-2">
                <p class="text-sm font-bold text-muted">
                  Usuário
                </p>
                <p class="break-all text-sm">
                  {{ usuario.username || "-" }}
                </p>
              </div>

              <div class="lg:col-span-1">
                <p class="text-sm font-bold text-muted">
                  Status
                </p>
                <UBadge
                  v-if="!usuario.bloqueado"
                  :label="usuario.ativo ? 'Ativo' : 'Inativo'"
                  :color="usuario.ativo ? 'success' : 'neutral'"
                  variant="subtle"
                  size="sm"
                />
                <UBadge
                  v-else
                  label="Conta bloqueada"
                  color="error"
                  variant="subtle"
                  size="sm"
                />
              </div>

              <div class="lg:col-span-2">
                <p class="text-sm font-bold text-muted">
                  Criado em
                </p>
                <span class="text-sm text-muted">
                  {{ formatarData(usuario.created_at) }}
                </span>
              </div>

              <div class="sm:col-span-2 lg:col-span-2">
                <p class="text-sm font-bold text-muted">
                  Ações
                </p>
                <div class="flex items-end gap-1">
                  <UButton
                    v-if="usuario.role === 'medico'"
                    icon="i-lucide-notebook-pen"
                    color="neutral"
                    variant="ghost"
                    size="sm"
                    class="min-h-11 min-w-11 sm:min-h-8 sm:min-w-8"
                    :aria-label="`Padrões de ${usuario.nome_completo}`"
                    title="Padrões"
                    @click="void(navigateTo(`/admin/padroes-medico/${usuario.id}`))"
                  />
                  <div
                    v-else
                    class="hidden sm:block sm:min-h-8 sm:min-w-8"
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
                    @click="void (confirmDeleteId = usuario.id)"
                  />
                  <UButton
                    v-if="usuario.bloqueado"
                    icon="i-lucide-lock-open"
                    color="success"
                    variant="ghost"
                    size="sm"
                    class="min-h-11 min-w-11 sm:min-h-8 sm:min-w-8"
                    :aria-label="`Desbloquear ${usuario.nome_completo}`"
                    title="Desbloquear conta"
                    @click="void(confirmUnlockId = usuario.id)"
                  />
                </div>
              </div>
            </div>
          </UPageCard>
        </div>
      </UCard>
    </div>

    <UsuarioFormModal
      v-if="editingUsuario"
      v-model:open="showFormModal"
      :usuario="editingUsuario"
      :role="editingUsuario.role"
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

    <ModalConfirmacao
      :abrir="confirmUnlockId !== null"
      titulo="Desbloquear conta?"
      descricao="O usuário poderá tentar fazer login novamente. Esta ação não altera o status ativo ou inativo da conta."
      texto-confirma="Desbloquear"
      cor-confirma="success"
      icone="lucide:lock-open"
      @fechar="confirmUnlockId = null"
      @confirmar="executarDesbloqueio"
    />
  </div>
</template>
