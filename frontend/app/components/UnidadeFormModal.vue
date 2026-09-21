<script setup lang="ts">
import FeatureUnidadeFormModal from '~/features/unidades/components/UnidadeFormModal.vue'

defineOptions({ inheritAttrs: false })
</script>

<template>
  <FeatureUnidadeFormModal v-bind="$attrs" />
</template>
