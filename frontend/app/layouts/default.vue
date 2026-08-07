<script setup lang="ts">
const auth = useAuthStore()

const unidadeAtivaLabel = computed(() => auth.activeClinica?.nome || 'Sem unidade')
const podeTrocarUnidade = computed(() => auth.clinicas.length > 1)

const navItems = [
  { label: 'Dashboard', icon: 'i-lucide-layout-dashboard', to: '/dashboard' },
  { label: 'Agenda', icon: 'i-lucide-calendar', to: '/agenda' },
  { label: 'Atendimento Médico', icon: 'i-lucide-stethoscope', to: '/atendimento-medico' },
  { label: 'Meus Pacientes', icon: 'i-lucide-users', to: '/pacientes' },
  { label: 'Padrões', icon: 'i-lucide-file-text', to: '/padroes-solicitacoes' }
]
</script>

<template>
  <div class="flex">
    <USidebar
      collapsible="icon"
      side="left"
    >
      <template #header>
        <NuxtLink to="/">
          <logoMed :isrecepcao="false" />
        </NuxtLink>
      </template>

      <UNavigationMenu
        orientation="vertical"
        :items="navItems"
      />

      <template #footer>
        <div class="mb-2 space-y-2 px-2">
          <UBadge
            :label="unidadeAtivaLabel"
            color="primary"
            variant="soft"
            class="w-full justify-center"
          />
          <UButton
            v-if="podeTrocarUnidade"
            icon="i-lucide-building-2"
            label="Trocar unidade"
            color="neutral"
            variant="ghost"
            class="w-full justify-start"
            to="/selecionar-clinica"
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
      </template>
    </USidebar>

    <div class="flex-1 flex flex-col min-h-screen">
      <UMain>
        <slot />
      </UMain>
    </div>
  </div>
</template>
