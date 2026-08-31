<script setup lang="ts">
definePageMeta({ layout: 'admin' })

const route = useRoute()
const usuariosStore = useUsuariosStore()
const openNav = inject<() => void>('openNav', () => {})

const medicoId = computed(() => Number(route.params.id))

const medico = computed(() =>
  usuariosStore.porRole('medico').find(u => u.id === medicoId.value)
)

const titulo = computed(() =>
  medico.value ? `Padroes — ${medico.value.nome_completo}` : 'Padroes do Medico'
)

onMounted(() => {
  if (!Number.isFinite(medicoId.value) || medicoId.value <= 0) {
    navigateTo('/admin/medicos')
    return
  }
  if (usuariosStore.porRole('medico').length === 0) {
    usuariosStore.fetchAll('medico')
  }
})
</script>

<template>
  <div>
    <UHeader
      :title="titulo"
      toggle-side="left"
    >
      <template #toggle>
        <UButton
          icon="i-lucide-panel-left"
          color="neutral"
          variant="ghost"
          class="min-h-11 min-w-11 lg:hidden"
          aria-label="Abrir menu"
          @click="openNav()"
        />
      </template>
      <template #left>
        <div class="flex min-w-0 items-center gap-2">
          <UButton
            icon="i-lucide-arrow-left"
            color="neutral"
            variant="ghost"
            size="sm"
            class="min-h-11 min-w-11 sm:min-h-8 sm:min-w-8"
            aria-label="Voltar para medicos"
            @click="void(navigateTo('/admin/medicos'))"
          />
          <p class="min-w-0 break-words text-lg font-semibold">
            {{ titulo }}
          </p>
        </div>
      </template>
      <template #right>
        <UColorModeButton />
      </template>
    </UHeader>

    <div class="min-h-screen bg-neutral-100 p-4 dark:bg-neutral-950 sm:p-6">
      <PadroesGerenciador :medico-id="Number.isFinite(medicoId) ? medicoId : null" />
    </div>
  </div>
</template>
