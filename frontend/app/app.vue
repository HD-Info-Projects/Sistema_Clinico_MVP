<script setup lang="ts">
import { pt_br as ptBR } from '@nuxt/ui/locale'

const auth = useAuthStore()
onMounted(() => auth.fetchUser())

const route = useRoute()
const layoutName = computed(() => {
  const path = route.path
  if (path === '/login' || path === '/selecionar-clinica') return 'auth'
  if (path.startsWith('/painel-chamada')) return 'tv'
  if (path === '/atendimento-medico') return 'atendimento'
  if (path.startsWith('/recepcao')) return 'recepcao'
  return 'default'
})

useHead({
  meta: [
    { name: 'viewport', content: 'width=device-width, initial-scale=1' }
  ],
  link: [
    { rel: 'icon', href: '/favicon.ico' }
  ],
  htmlAttrs: {
    lang: 'pt-BR'
  }
})

const title = 'MedSystem'
const description = 'Gestão clínica inteligente para o futuro da saúde.'

useSeoMeta({
  title,
  description,
  ogTitle: title,
  ogDescription: description
})
</script>

<template>
  <UApp :locale="ptBR">
    <NuxtLayout :name="layoutName">
      <NuxtPage :key="$route.fullPath" />
    </NuxtLayout>
  </UApp>
</template>
