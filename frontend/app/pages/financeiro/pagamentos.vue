<script setup lang="ts">
definePageMeta({ layout: 'financeiro' })

const openNav = inject<() => void>('openNav', () => {})
</script>

<template>
  <div class="p-4 sm:p-6">
    <header class="mb-6 flex items-center gap-3">
      <UButton
        icon="i-lucide-menu"
        aria-label="Alternar menu financeiro"
        color="neutral"
        variant="ghost"
        class="lg:hidden"
        @click="openNav"
      />
      <h1 class="text-xl font-semibold text-highlighted">
        Gerenciamento de pagamentos
      </h1>
    </header>

    <!-- Desenhe aqui a listagem de pagamentos e os links para /financeiro/pacientes/:id. -->
    <div class="min-h-80 rounded-lg border border-dashed border-default" />
  </div>
</template>
