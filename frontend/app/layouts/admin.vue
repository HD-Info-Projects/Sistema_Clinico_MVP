<script setup lang="ts">
const auth = useAuthStore()

const navItems = [
  { label: 'Dashboard', icon: 'i-lucide-layout-dashboard', to: '/admin' },
  { label: 'Medicos', icon: 'i-lucide-stethoscope', to: '/admin/medicos' },
  { label: 'Recepcionistas', icon: 'i-lucide-user-plus', to: '/admin/recepcao' },
  { label: 'Administradores', icon: 'i-lucide-shield', to: '/admin/admins' },
  { label: 'Unidades', icon: 'i-lucide-building', to: '/admin/unidades' }
]
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
        <UButton
          icon="i-lucide-log-out"
          label="Sair"
          color="neutral"
          variant="ghost"
          class="w-full justify-start"
          @click="auth.logout()"
        />
      </template>
    </USidebar>

    <div class="flex-1 flex flex-col min-h-screen">
      <UMain>
        <slot />
      </UMain>
    </div>
  </div>
</template>
