<script setup lang="ts">
const auth = useAuthStore()

const unidadeAtivaLabel = computed(() => auth.activeClinica?.nome || 'Sem unidade')
const podeTrocarUnidade = computed(() => auth.clinicas.length > 1)

const navItems = [
  { label: 'Dashboard', icon: 'i-lucide-layout-dashboard', to: '/recepcao' },
  { label: 'Agenda', icon: 'i-lucide-calendar', to: '/recepcao/agenda' },
  { label: 'Cadastro de Pacientes', icon: 'i-lucide-user-plus', to: '/recepcao/cadastro-pacientes' },
  { label: 'Cadastro de Atendimento', icon: 'i-lucide-user-check', to: '/recepcao/cadastro-atendimento' },
  { label: 'No-show', icon: 'i-lucide-user-x', to: '/recepcao/noshow' },
  { label: 'Conversão de Exames', icon: 'i-lucide-flask-conical', to: '/recepcao/retencao-exames' }
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
        <NuxtLink to="/recepcao">
          <logoMed :tipo="1" />
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
            <UButton
              v-if="auth.isAdmin"
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
