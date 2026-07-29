<script setup lang="ts">
const auth = useAuthStore()

const navItems = [
  { label: 'Dashboard', icon: 'i-lucide-layout-dashboard', to: '/recepcao' },
  { label: 'Agenda', icon: 'i-lucide-calendar', to: '/recepcao/agenda' },
  // { label: 'Cadastro', icon: 'i-lucide-user-plus', to: '/recepcao/cadastro' },
  { label: 'No-show', icon: 'i-lucide-user-x', to: '/recepcao/noshow' },
  { label: 'Conversão de Exames', icon: 'i-lucide-flask-conical', to: '/recepcao/retencao-exames' }
]
</script>

<template>
  <div class="flex">
    <USidebar
      collapsible="icon"
      side="left"
    >
      <template #header>
        <NuxtLink to="/recepcao">
          <logoMed isrecepcao />
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
