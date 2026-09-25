<script setup lang="ts">
definePageMeta({ layout: 'admin' })
</script>

<template>
  <UsuarioListagem
    role="coord_financeiro"
    titulo="Coordenadores Financeiros"
    placeholder-busca="Buscar por nome ou email..."
  />
</template>
