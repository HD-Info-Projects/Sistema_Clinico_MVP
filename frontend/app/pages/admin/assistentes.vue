<script setup lang="ts">
definePageMeta({ layout: 'admin' })
</script>

<template>
  <UsuarioListagem
    role="assistente"
    titulo="Assistentes"
    placeholder-busca="Buscar por nome, email ou médico vinculado..."
  />
</template>
