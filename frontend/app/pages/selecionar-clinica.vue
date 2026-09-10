<script setup lang="ts">
import { paginaInicialPorModo } from '~/stores/auth'

const auth = useAuthStore()

const loading = ref(false)

const subtitulo = computed(() => {
  if (auth.isAdmin && auth.accessMode === 'recepcionista') {
    return 'Escolha a unidade na qual deseja atender como recepcionista.'
  }
  return 'Você tem acesso a mais de uma clínica. Escolha qual deseja acessar.'
})

async function selecionar(id: number) {
  if (loading.value) return
  loading.value = true
  const selecionou = await auth.setActiveClinica(id)
  if (!selecionou) {
    loading.value = false
    return
  }

  if (auth.isAdmin) {
    navigateTo(paginaInicialPorModo(auth.accessMode))
  } else if (auth.isRecepcao) {
    navigateTo('/recepcao')
  } else {
    navigateTo('/dashboard')
  }
}
</script>

<template>
  <div class="relative z-10 m-auto w-[calc(100%-2rem)] max-w-lg rounded-xl bg-default/95 p-4 shadow-xl sm:p-6">
    <h1 class="text-xl font-bold mb-2">
      Selecione a Unidade
    </h1>
    <p class="text-muted mb-6">
      {{ subtitulo }}
    </p>

    <div class="flex flex-col gap-3">
      <UCard
        v-for="c in auth.clinicas"
        :key="c.id"
        role="button"
        :tabindex="loading ? -1 : 0"
        :aria-disabled="loading"
        :ui="{ root: 'cursor-pointer hover:ring-2 hover:ring-primary transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary aria-disabled:cursor-wait aria-disabled:opacity-70 motion-reduce:transition-none' }"
        @click="selecionar(c.id)"
        @keydown.enter="selecionar(c.id)"
        @keydown.space.prevent="selecionar(c.id)"
      >
        <div class="flex min-w-0 items-center gap-3">
          <div class="flex size-10 shrink-0 items-center justify-center rounded-full bg-primary/10">
            <UIcon
              name="i-lucide-building-2"
              class="text-primary"
            />
          </div>
          <div class="min-w-0">
            <p class="font-semibold">
              {{ c.nome }}
            </p>
            <p class="text-sm text-muted">
              {{ c.endereco }}
            </p>
          </div>
        </div>
      </UCard>
    </div>
  </div>
</template>
