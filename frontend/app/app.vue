<script setup lang="ts">
import { pt_br as ptBR } from '@nuxt/ui/locale'

const auth = useAuthStore()
const route = useRoute()

onMounted(() => {
  if (route.path.startsWith('/painel-chamada')) return
  void auth.fetchUser()
})

const layoutName = computed(() => {
  const path = route.path
  if (path === '/login' || path === '/selecionar-clinica' || path === '/selecionar-acesso') return 'auth'
  if (path.startsWith('/painel-chamada')) return 'tv'
  if (path === '/atendimento-medico') return 'atendimento'
  if (path.startsWith('/recepcao')) return 'recepcao'
  if (path.startsWith('/admin')) return 'admin'
  return 'default'
})

const hasLayout = computed(() => route.path !== '/acesso-negado')
const hasMainTarget = computed(() => !['tv', 'atendimento'].includes(layoutName.value))

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
    <a
      v-if="hasMainTarget"
      href="#conteudo-principal"
      class="fixed left-4 top-4 z-[100] -translate-y-20 rounded-md bg-primary px-4 py-2 font-medium text-inverted shadow-lg transition-transform focus:translate-y-0 focus:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2 motion-reduce:transition-none"
    >
      Pular para o conteúdo principal
    </a>
    <NuxtLayout
      v-if="hasLayout"
      :name="layoutName"
    >
      <NuxtPage :key="$route.fullPath" />
    </NuxtLayout>
    <NuxtPage
      v-else
      :key="$route.fullPath"
    />
  </UApp>
</template>
