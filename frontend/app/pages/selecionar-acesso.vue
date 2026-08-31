<script setup lang="ts">
import { paginaInicialPorModo, type AccessMode } from '~/stores/auth'

const auth = useAuthStore()

if (!auth.user && import.meta.client) {
  await auth.fetchUser()
}

const opcoes: { modo: AccessMode, titulo: string, descricao: string, icone: string }[] = [
  {
    modo: 'recepcionista',
    titulo: 'Entrar como Recepcionista',
    descricao: 'Fila de atendimento, agenda da recepção e no-show.',
    icone: 'i-lucide-concierge-bell'
  },
  {
    modo: 'administrador',
    titulo: 'Painel Administrativo',
    descricao: 'Gerenciamento de usuários, unidades e administração do sistema.',
    icone: 'i-lucide-settings'
  },
  {
    modo: 'logs',
    titulo: 'Logs de Auditoria',
    descricao: 'Consulta aos registros de auditoria LGPD.',
    icone: 'i-lucide-scroll-text'
  }
]

function selecionar(modo: AccessMode) {
  auth.setAccessMode(modo)

  if (modo === 'recepcionista' && auth.clinicas.length !== 1) {
    navigateTo('/selecionar-clinica')
    return
  }

  navigateTo(paginaInicialPorModo(modo))
}
</script>

<template>
  <div class="relative z-10 m-auto w-[calc(100%-2rem)] max-w-lg rounded-xl bg-default/95 p-4 shadow-xl sm:p-6">
    <h1 class="text-xl font-bold mb-2">
      Selecione o Acesso
    </h1>
    <p class="text-muted mb-6">
      Escolha como deseja acessar o sistema.
    </p>

    <div class="flex flex-col gap-3">
      <UCard
        v-for="opcao in opcoes"
        :key="opcao.modo"
        role="button"
        tabindex="0"
        :ui="{ root: 'cursor-pointer hover:ring-2 hover:ring-primary transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary motion-reduce:transition-none' }"
        @click="selecionar(opcao.modo)"
        @keydown.enter="selecionar(opcao.modo)"
        @keydown.space.prevent="selecionar(opcao.modo)"
      >
        <div class="flex min-w-0 items-center gap-3">
          <div class="flex size-10 shrink-0 items-center justify-center rounded-full bg-primary/10">
            <UIcon
              :name="opcao.icone"
              class="text-primary"
            />
          </div>
          <div class="min-w-0">
            <p class="font-semibold">
              {{ opcao.titulo }}
            </p>
            <p class="text-sm text-muted">
              {{ opcao.descricao }}
            </p>
          </div>
        </div>
      </UCard>
    </div>
  </div>
</template>
