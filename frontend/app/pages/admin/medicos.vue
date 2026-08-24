<script setup lang="ts">
definePageMeta({ layout: 'admin' })
</script>

<template>
  <UsuarioListagem
    role="medico"
    titulo="Medicos"
    placeholder-busca="Buscar por nome, CRM ou especialidade..."
  />
</template>
