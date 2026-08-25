<script setup lang="ts">
definePageMeta({ layout: 'admin' })
</script>

<template>
  <UsuarioListagem
    role="admin"
    titulo="Administradores"
    placeholder-busca="Buscar por nome ou email..."
  />
</template>
