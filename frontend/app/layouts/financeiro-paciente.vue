<script setup lang="ts">
const open = ref(true)
const route = useRoute()
const isMobile = useMediaQuery('(max-width: 1023px)')

watch(() => route.fullPath, () => {
  if (isMobile.value) open.value = false
})
</script>

<template>
  <div class="flex h-dvh min-h-0 min-w-0 overflow-hidden">
    <USidebar
      v-model:open="open"
      collapsible="offcanvas"
      title="Informações do paciente"
      :style="{ '--sidebar-width': 'min(35rem, 100vw)' }"
      class="max-w-full min-h-0 shrink-0"
    >
      <template #header>
        <UButton
          to="/financeiro/pagamentos"
          icon="i-lucide-arrow-left"
          label="Voltar para pagamentos"
          color="neutral"
          variant="ghost"
        />
      </template>

      <slot name="sidebar" />
    </USidebar>

    <UMain
      id="conteudo-principal"
      tabindex="-1"
      class="min-h-0 min-w-0 flex-1 overflow-y-auto"
    >
      <div class="flex items-center gap-3 border-b border-default px-4 py-4 sm:px-6">
        <UButton
          icon="i-lucide-menu"
          aria-label="Alternar informações do paciente"
          color="neutral"
          variant="ghost"
          class="lg:hidden"
          @click="open = !open"
        />
        <h1 class="text-xl font-semibold text-highlighted">
          Gerenciamento do paciente
        </h1>
      </div>

      <div class="p-4 sm:p-6">
        <slot />
      </div>
    </UMain>
  </div>
</template>
