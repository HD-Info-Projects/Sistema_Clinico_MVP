<script setup lang="ts">
definePageMeta({ layout: 'admin' })

const auth = useAuthStore()
const usuariosStore = useUsuariosStore()
const unidadesStore = useUnidadesStore()

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

const colunas = [
  { accessorKey: 'nome', header: 'Nome' },
  { accessorKey: 'role', header: 'Perfil' },
  { accessorKey: 'email', header: 'Email' },
  { accessorKey: 'created_at', header: 'Criado em' }
]

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
    <UHeader title="Dashboard Administrativo">
      <template #right>
        <UBadge
          :label="userName"
          color="neutral"
          variant="soft"
        />
        <UColorModeButton />
      </template>
    </UHeader>

    <div class="p-6 bg-neutral-100 dark:bg-neutral-950 min-h-screen space-y-6">
      <div>
        <p class="text-3xl font-semibold">
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

        <UTable
          v-else
          :columns="colunas"
          :data="ultimosUsuarios"
        >
          <template #nome-cell="{ row }">
            <div class="flex items-center gap-3">
              <UAvatar
                :alt="row.original.nome_completo"
                color="primary"
                size="sm"
              />
              <p class="font-medium">
                {{ row.original.nome_completo }}
              </p>
            </div>
          </template>

          <template #role-cell="{ row }">
            <UBadge
              :label="rotuloRole(row.original.role)"
              :color="corRole(row.original.role)"
              variant="subtle"
            />
          </template>

          <template #created_at-cell="{ row }">
            <span class="text-sm text-muted">
              {{ formatarData(row.original.created_at) }}
            </span>
          </template>
        </UTable>
      </UCard>
    </div>
  </div>
</template>
