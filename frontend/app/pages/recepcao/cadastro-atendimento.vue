<script setup lang="ts">
const auth = useAuthStore()

const userName = computed(() => auth.user?.nome || 'Usuário')

const items = [
  {
    label: 'Responsável pelo paciente',
    icon: 'i-lucide-users',
    slot: 'cadastro'
  }
]
</script>

<template>
  <div>
    <UHeader title="Cadastro de Pacientes">
      <template #right>
        <div class="flex items-center gap-2">
          <UBadge
            :label="userName"
            color="neutral"
            variant="soft"
          />
          <UColorModeButton />
        </div>
      </template>
    </UHeader>

    <div class="min-h-screen space-y-4 bg-muted p-4 sm:space-y-6 sm:p-6">
      <UCard>
        <template #header>
          <h3 class="font-semibold">
            Cadastro
          </h3>
        </template>

        <UForm
          class="space-y-4"
        >
          <UFormField
            label="Nome"
            name="nome"
          >
            <UInput />
          </UFormField>

          <UFormField
            label="Email"
            name="email"
          >
            <UInput

              type="email"
            />
          </UFormField>

          <UButton
            type="submit"
            label="Cadastrar"
          />
        </UForm>
      </UCard>

      <UPageCard
        :ui="{ container: 'p-2 sm:p-2 sm:px-4' }"
      >
        <UAccordion :items="items">
          <template #cadastro>
            <UForm
              class="space-y-4"
            >
              <UFormField
                label="Nome"
                name="nome"
              >
                <UInput />
              </UFormField>

              <UFormField
                label="Email"
                name="email"
              >
                <UInput

                  type="email"
                />
              </UFormField>

              <UButton
                type="submit"
                label="Cadastrar"
              />
            </UForm>
          </template>
        </UAccordion>
      </UPageCard>
    </div>
  </div>
</template>
