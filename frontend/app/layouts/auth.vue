<script setup lang="ts">
import type { PageFeatureProps } from '@nuxt/ui'

const features = ref<PageFeatureProps[]>([
  {
    title: '+15k',
    description: 'PROFISSIONAIS',
    icon: 'i-lucide-user'
  },
  {
    title: '99.9%',
    description: 'UPTIME',
    icon: 'i-lucide-clock'
  }
])
</script>

<template>
  <div class="flex h-dvh min-w-0 overflow-hidden">
    <aside
      class="relative hidden h-full w-1/2 shrink-0 overflow-hidden lg:block"
      aria-label="Sobre o MedSystem"
    >
      <NuxtImg
        src="img/bg-login.png"
        class="absolute inset-0 w-full h-full object-cover"
        alt=""
      />
      <div class="absolute inset-0 bg-primary-800/80" />
      <UPageSection
        class="relative flex h-full items-center"
        title="Gestão clínica inteligente para o futuro da saúde."
        description="Centralize Consultas Médicas, Prontuários e Agendamentos em uma plataforma única, segura e projetada para profissionais de alta performance."
        :ui="{
          root: 'text-white',
          title: 'text-white font-medium text-left',
          description: 'text-white text-left',
          headline: 'pb-15',
          features: 'grid grid-cols-2 gap-6'
        }"
      >
        <template #headline>
          <div class="flex items-center gap-3">
            <UBadge
              icon="medical-icon:health-services"
              size="xl"
              variant="soft"
              class="bg-white scale-120"
            />
            <div>
              <p class="text-2xl font-medium">
                MedSystem
              </p>
              <p class="text-sm font-medium text-white">
                Gestão médica
              </p>
            </div>
          </div>
        </template>

        <template #features>
          <UPageFeature
            v-for="feature in features"
            :key="feature.title"
            as="li"
            :title="feature.title"
            :description="feature.description"
            :icon="feature.icon"
            :ui="{
              root: 'text-white items-center justify-center text-center',
              title: 'text-white text-center text-2xl',
              description: 'text-white text-center',
              leadingIcon: 'size-8 text-primary-200'
            }"
          />
        </template>
      </UPageSection>
    </aside>
    <main
      id="conteudo-principal"
      tabindex="-1"
      class="relative flex h-full min-w-0 w-full items-center justify-center overflow-y-auto bg-[url('/img/bg-login.png')] bg-cover bg-center lg:w-1/2 lg:bg-none"
    >
      <div class="absolute inset-0 bg-primary-800/80 lg:hidden" />
      <slot />
    </main>
  </div>
</template>
