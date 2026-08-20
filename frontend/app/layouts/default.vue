<script setup lang="ts">
const auth = useAuthStore()

const unidadeAtivaLabel = computed(() => auth.activeClinica?.nome || 'Sem unidade')
const podeTrocarUnidade = computed(() => auth.clinicas.length > 1)

const navItems = computed(() => [
  ...(auth.user?.role === 'medico'
    ? [
        { label: 'Dashboard', icon: 'i-lucide-layout-dashboard', to: '/dashboard' },
        { label: 'Agenda', icon: 'i-lucide-calendar', to: '/agenda' },
        { label: 'Atendimento Médico', icon: 'i-lucide-stethoscope', to: '/atendimento-medico' },
        { label: 'Meus Pacientes', icon: 'i-lucide-users', to: '/pacientes' },
        { label: 'Padrões', icon: 'i-lucide-file-text', to: '/padroes-solicitacoes' }
      ]
    : []),
  ...(['admin', 'dpo', 'ti'].includes(auth.user?.role || '')
    ? [{ label: 'Auditoria LGPD', icon: 'i-lucide-shield-check', to: '/lgpd/auditoria' }]
    : [])
])
</script>

<template>
  <div class="flex">
    <USidebar
      collapsible="icon"
      side="left"
    >
      <template #header>
        <NuxtLink to="/">
          <logoMed :tipo="0" />
        </NuxtLink>
      </template>

      <UNavigationMenu
        orientation="vertical"
        :items="navItems"
      />

      <template #footer>
        <div class="felx flex-col gap-2 w-full">
          <div class="mb-2 flex flex-col gap-2 px-2">
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
