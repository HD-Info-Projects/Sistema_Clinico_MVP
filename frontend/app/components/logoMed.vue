<script setup lang="ts">
const props = defineProps<{
  tipo: number
}>()
</script>

<template>
  <div class="flex items-center gap-3">
    <UBadge
      icon="medical-icon:health-services"
      size="md"
      variant="solid"
      class=" scale-120 p-2"
    />
    <div>
      <p class="text-2xl font-bold">
        MedSystem
      </p>
      <p class="text-sm font-light text-muted">
        {{ props.tipo === 0 ? 'Gestão clínica'
          :props.tipo === 1 ? 'Gestão médica' : 'ADMINISTRAÇÃO' }}
      </p>
    </div>
  </div>
</template>
