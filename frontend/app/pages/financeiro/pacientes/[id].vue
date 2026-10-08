<script setup lang="ts">
// O layout explícito permite editar a lateral e o conteúdo nesta mesma página.
definePageMeta({ layout: false })
</script>

<template>
  <NuxtLayout name="financeiro-paciente">
    <template #sidebar>
      <h2 class="font-semibold text-highlighted">
        Informações do paciente
      </h2>
      <!-- Desenhe aqui as informações da barra lateral. -->
      <div class="min-h-80 rounded-lg border border-dashed border-default" />
    </template>

    <!-- Desenhe aqui o conteúdo principal do gerenciamento do paciente. -->
    <div class="min-h-80 rounded-lg border border-dashed border-default" />
  </NuxtLayout>
</template>
