<script setup lang="ts">
const auth = useAuthStore()

const navItems = [
  { label: 'Dashboard', icon: 'i-lucide-layout-dashboard', to: '/admin' },
  { label: 'Medicos', icon: 'i-lucide-stethoscope', to: '/admin/medicos' },
  { label: 'Recepcionistas', icon: 'i-lucide-user-plus', to: '/admin/recepcao' },
  { label: 'Administradores', icon: 'i-lucide-shield', to: '/admin/admins' },
  { label: 'Unidades', icon: 'i-lucide-building', to: '/admin/unidades' }
]

function trocarAcesso() {
  auth.limparAccessMode()
  navigateTo('/selecionar-acesso')
}
</script>

<template>
  <div class="flex">
    <USidebar
      collapsible="icon"
      side="left"
    >
      <template #header>
        <NuxtLink to="/admin">
          <logoMed :tipo="2" />
        </NuxtLink>
      </template>

      <UNavigationMenu
        orientation="vertical"
        :items="navItems"
      />

      <template #footer>
        <div class="felx flex-col gap-2 w-full">
          <div class="mb-2 flex flex-col gap-2 px-2">
            <UButton
              icon="i-lucide-repeat"
              label="Trocar acesso"
              color="neutral"
              variant="ghost"
              class="w-full justify-start"
              @click="trocarAcesso()"
            />
          </div>
          <UButton
            icon="i-lucide-log-out"
            label="Sair"
            color="neutral"
            variant="ghost"
            class="w-full justify-start"
            @click="auth.logout()"
          />
        </div>
      </template>
    </USidebar>

    <div class="flex-1 flex flex-col min-h-screen">
      <UMain>
        <slot />
      </UMain>
    </div>
  </div>
</template>
