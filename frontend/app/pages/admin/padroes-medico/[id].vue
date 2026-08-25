<script setup lang="ts">
definePageMeta({ layout: 'admin' })

const route = useRoute()
const usuariosStore = useUsuariosStore()

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
    <UHeader :title="titulo">
      <template #left>
        <div class="flex items-center gap-2">
          <UButton
            icon="i-lucide-arrow-left"
            color="neutral"
            variant="ghost"
            size="sm"
            aria-label="Voltar para medicos"
            @click="void(navigateTo('/admin/medicos'))"
          />
          <p class="text-lg font-semibold whitespace-nowrap">
            {{ titulo }}
          </p>
        </div>
      </template>
      <template #right>
        <UColorModeButton />
      </template>
    </UHeader>

    <div class="p-6 bg-neutral-100 dark:bg-neutral-950 min-h-screen">
      <PadroesGerenciador :medico-id="Number.isFinite(medicoId) ? medicoId : null" />
    </div>
  </div>
</template>
