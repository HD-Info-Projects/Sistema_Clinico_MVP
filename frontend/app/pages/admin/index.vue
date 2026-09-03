<script setup lang="ts">
definePageMeta({ layout: 'admin' })

const auth = useAuthStore()
const usuariosStore = useUsuariosStore()
const unidadesStore = useUnidadesStore()
const openNav = inject<() => void>('openNav', () => {})

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
</script>

<template>
  <div>
    <UHeader
      title="Dashboard Administrativo"
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

    <div class="min-h-screen space-y-6 bg-neutral-100 p-4 dark:bg-neutral-950 sm:p-6">
      <div class="min-w-0">
        <p class="break-words text-2xl font-semibold sm:text-3xl">
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
              <div class="lg:col-span-4">
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

              <div class="lg:col-span-4">
                <p class="text-sm font-bold text-muted">
                  Email
                </p>
                <p class="break-all text-sm">
                  {{ usuario.email }}
                </p>
              </div>

              <div class="lg:col-span-2">
                <p class="text-sm font-bold text-muted">
                  Criado em
                </p>
                <span class="text-sm text-muted">
                  {{ formatarData(usuario.created_at) }}
                </span>
              </div>
            </div>
          </UPageCard>
        </div>
      </UCard>
    </div>
  </div>
</template>
