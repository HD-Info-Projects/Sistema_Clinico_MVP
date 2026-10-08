<script setup lang="ts">
definePageMeta({ layout: 'admin' })
</script>

<template>
  <UsuarioListagem
    role="financeiro"
    titulo="Financeiro"
    placeholder-busca="Buscar por nome ou email..."
  />
</template>
