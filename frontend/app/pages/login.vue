<script setup lang="ts">
import * as z from 'zod'
import type { FormSubmitEvent, AuthFormField } from '@nuxt/ui'
import { useAuthStore } from '~/stores/auth'

const auth = useAuthStore()
const loading = ref(false)
const errorMsg = ref('')

const fields: AuthFormField[] = [{
  name: 'email',
  type: 'email',
  label: 'Email',
  placeholder: 'Digite seu email',
  required: true
}, {
  name: 'password',
  label: 'Senha',
  type: 'password',
  placeholder: 'Digite sua senha',
  required: true
}, {
  name: 'remember',
  label: 'Mantenha-me conectado',
  type: 'checkbox'
}]

const schema = z.object({
  email: z.string('O email é obrigatório.').email('Email inválido'),
  password: z.string('A senha é obrigatória.').min(8, 'A senha deve ter pelo menos 8 caracteres')
})

type Schema = z.output<typeof schema>

async function onSubmit(payload: FormSubmitEvent<Schema>) {
  loading.value = true
  errorMsg.value = ''

  const result = await auth.login(payload.data)

  if (!result.success) {
    errorMsg.value = result.message || 'Erro ao realizar login'
  }

  loading.value = false
}
</script>

<template>
  <div class="relative z-10 w-full p-4 sm:p-6">
    <UPageCard class="w-full max-w-md">
      <UAuthForm
        :submit="{
          label: 'Entrar',
          icon: 'i-lucide-log-in',
          color: 'primary',
          variant: 'solid',
          loading: loading
        }"
        :schema="schema"
        title="Bem vindo de volta!"
        description="Acesse sua conta para gerenciar seus pacientes."
        :fields="fields"
        :ui="{ leading: 'flex items-center justify-center' }"
        @submit="onSubmit"
      >
        <template #leading>
          <NuxtImg
            src="img/logo.png"
            alt="MedSystem"

            height="50"
          />
        </template>

        <template #validation>
          <UAlert
            v-if="errorMsg"
            :title="errorMsg"
            description="Verifique suas credenciais e tente novamente."
            color="error"
            icon="i-lucide-info"
            variant="subtle"
            class="mb-4"
          />
        </template>

        <template #footer>
          <div class="flex w-full flex-wrap justify-center gap-4">
            <span class="text-sm text-muted flex items-center gap-1">
              <UIcon name="i-lucide-shield-check" />
              LGPD Compliant
            </span>
            <span class="text-sm text-muted flex items-center gap-1">
              <UIcon name="i-lucide-shield" />
              SSL Secure
            </span>
          </div>
        </template>
      </UAuthForm>
    </UPageCard>
  </div>
</template>
