<script setup lang="ts">
const auth = useAuthStore()

const open = ref(true)
const isDesktop = useMediaQuery('(min-width: 1024px)')
const route = useRoute()

watch(
  () => route.fullPath,
  () => {
    if (!isDesktop.value) open.value = false
  }
)

provide('openNav', () => {
  open.value = !open.value
})

const unidadeAtivaLabel = computed(() => auth.activeClinica?.nome || 'Sem unidade')
const podeTrocarUnidade = computed(() => auth.clinicas.length > 1)

function trocarUnidade() {
  if (!isDesktop.value) open.value = false
  return navigateTo('/selecionar-clinica')
}

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

function trocarAcesso() {
  auth.limparAccessMode()
  navigateTo('/selecionar-acesso')
}
</script>

<template>
  <div class="flex min-h-dvh min-w-0">
    <USidebar
      v-model:open="open"
      collapsible="icon"
      :menu="{
        ui: {
          content: 'w-64'
        }
      }"
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
        <div class="flex w-full flex-col gap-2">
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
              @click="trocarUnidade()"
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
