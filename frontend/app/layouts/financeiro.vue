<script setup lang="ts">
const auth = useAuthStore()
const route = useRoute()
const open = ref(true)
const isDesktop = useMediaQuery('(min-width: 1024px)')

watch(() => route.fullPath, () => {
  if (!isDesktop.value) open.value = false
})

provide('openNav', () => {
  open.value = !open.value
})

const navItems = [
  { label: 'Pagamentos', icon: 'i-lucide-wallet', to: '/financeiro/pagamentos' },
  { label: 'Conciliação de cartões', icon: 'i-lucide-credit-card', to: '/financeiro/conciliacao-cartoes' }
]

function trocarAcesso() {
  auth.limparAccessMode()
  void navigateTo('/selecionar-acesso')
}
</script>

<template>
  <div class="flex min-h-dvh min-w-0">
    <USidebar
      v-model:open="open"
      collapsible="icon"
      :menu="{ ui: { content: 'w-64' } }"
      side="left"
    >
      <template #header>
        <NuxtLink to="/financeiro/pagamentos">
          <logoMed :tipo="1" />
        </NuxtLink>
      </template>

      <UNavigationMenu
        orientation="vertical"
        :items="navItems"
      />

      <template #footer>
        <div class="flex w-full flex-col gap-2">
          <UBadge
            :label="auth.activeClinica?.nome || 'Sem unidade'"
            color="primary"
            variant="soft"
            class="w-full justify-center"
          />
          <UButton
            v-if="auth.clinicas.length > 1"
            to="/selecionar-clinica"
            icon="i-lucide-building-2"
            label="Trocar unidade"
            color="neutral"
            variant="ghost"
            class="w-full justify-start"
          />
          <UButton
            v-if="auth.isAdmin"
            icon="i-lucide-repeat"
            label="Trocar acesso"
            color="neutral"
            variant="ghost"
            class="w-full justify-start"
            @click="trocarAcesso"
          />
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

    <div class="flex min-h-dvh min-w-0 flex-1 flex-col">
      <UMain
        id="conteudo-principal"
        tabindex="-1"
        class="min-w-0"
      >
        <slot />
      </UMain>
    </div>
  </div>
</template>
