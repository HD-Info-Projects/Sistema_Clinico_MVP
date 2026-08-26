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
  <div class="w-full max-w-lg mx-auto p-6">
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
        :ui="{ root: 'cursor-pointer hover:ring-2 hover:ring-primary transition-all' }"
        @click="selecionar(c.id)"
      >
        <div class="flex items-center gap-3">
          <div class="size-10 rounded-full bg-primary/10 flex items-center justify-center">
            <UIcon
              name="i-lucide-building-2"
              class="text-primary"
            />
          </div>
          <div>
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
