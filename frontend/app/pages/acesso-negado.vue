<script setup lang="ts">
definePageMeta({ layout: false })

const auth = useAuthStore()

const destinoPrincipal = computed(() => {
  if (['admin', 'dpo', 'ti'].includes(auth.user?.role || '')) return '/lgpd/auditoria'
  if (auth.user?.role === 'recepcao') return '/recepcao'
  return '/dashboard'
})
</script>

<template>
  <main
    id="conteudo-principal"
    tabindex="-1"
    class="flex min-h-dvh items-center justify-center bg-slate-50 px-4 py-6"
  >
    <UCard class="max-w-lg w-full">
      <div class="space-y-6 text-center">
        <div class="mx-auto size-14 rounded-full bg-red-50 text-red-600 flex items-center justify-center">
          <UIcon
            name="i-lucide-shield-alert"
            class="size-7"
          />
        </div>

        <div class="space-y-2">
          <h1 class="text-2xl font-semibold text-slate-900">
            Acesso negado
          </h1>
          <p class="text-slate-600">
            Seu perfil não possui permissão para acessar esta área do sistema.
          </p>
        </div>

        <div class="flex flex-col sm:flex-row gap-3 justify-center">
          <UButton
            label="Voltar para início"
            icon="i-lucide-arrow-left"
            color="primary"
            @click="void(navigateTo(destinoPrincipal))"
          />
          <UButton
            label="Sair"
            icon="i-lucide-log-out"
            color="neutral"
            variant="soft"
            @click="auth.logout()"
          />
        </div>
      </div>
    </UCard>
  </main>
</template>
