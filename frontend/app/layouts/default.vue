<script setup lang="ts">
const auth = useAuthStore()

const open = ref(true)
const isDesktop = useMediaQuery('(min-width: 1024px)')
const route = useRoute()

watch(
  () => route.fullPath,
  () => {
    if (!isDesktop.value) open.value = false
  }
)

provide('openNav', () => {
  open.value = !open.value
})

const unidadeAtivaLabel = computed(() => auth.activeClinica?.nome || 'Sem unidade')
const podeTrocarUnidade = computed(() => auth.clinicas.length > 1)

function trocarUnidade() {
  if (!isDesktop.value) open.value = false
  return navigateTo('/selecionar-clinica')
}

const navItems = computed(() => [
  ...(auth.user?.role === 'medico'
    ? [
        { label: 'Dashboard', icon: 'i-lucide-layout-dashboard', to: '/dashboard' },
        { label: 'Agenda', icon: 'i-lucide-calendar', to: '/agenda' },
        { label: 'Atendimento Médico', icon: 'i-lucide-stethoscope', to: '/atendimento-medico' },
        { label: 'Meus Pacientes', icon: 'i-lucide-users', to: '/pacientes' },
        { label: 'Padrões', icon: 'i-lucide-file-text', to: '/padroes-solicitacoes' }
      ]
    : []),
  ...(['admin', 'dpo', 'ti'].includes(auth.user?.role || '')
    ? [{ label: 'Auditoria LGPD', icon: 'i-lucide-shield-check', to: '/lgpd/auditoria' }]
    : [])
])

function trocarAcesso() {
  auth.limparAccessMode()
  navigateTo('/selecionar-acesso')
}

const agendamentosStore = useAgendamentosStore()
const verificandoLogout = ref(false)
const modalLogoutBloqueadoAberto = ref(false)
const carregandoAtendimento = ref(false)
const atendimentoBloqueanteId = ref<number | null>(null)
const pacienteEmAtendimentoNome = ref<string | null>(null)
const dataAtendimentoEmAndamento = ref<string | null>(null)
const toast = useToast()

async function tentarSair() {
  if (verificandoLogout.value) return
  atendimentoBloqueanteId.value = null
  pacienteEmAtendimentoNome.value = null
  dataAtendimentoEmAndamento.value = null

  if (auth.user?.role !== 'medico') {
    await auth.logout()
    return
  }

  verificandoLogout.value = true
  try {
    const resultado = await auth.logout()
    if (!resultado.success && resultado.reason === 'atendimento') {
      atendimentoBloqueanteId.value = resultado.atendimentoId
      pacienteEmAtendimentoNome.value = resultado.pacienteNome
      dataAtendimentoEmAndamento.value = resultado.data
      modalLogoutBloqueadoAberto.value = true
      return
    }
  } finally {
    verificandoLogout.value = false
  }
}

async function irParaAtendimento() {
  if (carregandoAtendimento.value) return

  carregandoAtendimento.value = true
  const dataAtendimento = dataAtendimentoEmAndamento.value || formatarDataISO(new Date())
  try {
    await agendamentosStore.fetchAgendamentos(
      auth.activeClinicaId ?? undefined,
      dataAtendimento,
      auth.user?.id
    )

    const atendimento = atendimentoBloqueanteId.value
      ? agendamentosStore.agendamentos.find(item => item.id === atendimentoBloqueanteId.value)
      : agendamentosStore.emAtendimento
    if (!atendimento || atendimento.status !== 'em-atendimento') {
      toast.add({
        title: 'Atendimento não encontrado',
        description: 'Atualize a página e tente novamente.',
        color: 'error',
        icon: 'i-lucide-alert-circle'
      })
      return
    }

    agendamentosStore.focarAtendimento(atendimento)
    modalLogoutBloqueadoAberto.value = false
    await navigateTo('/atendimento-medico')
  } finally {
    carregandoAtendimento.value = false
  }
}

function fecharModalLogout() {
  modalLogoutBloqueadoAberto.value = false
  atendimentoBloqueanteId.value = null
  dataAtendimentoEmAndamento.value = null
}
</script>

<template>
  <div class="flex min-h-dvh min-w-0">
    <USidebar
      v-model:open="open"
      collapsible="icon"
      :menu="{
        ui: {
          content: 'w-64'
        }
      }"
      side="left"
    >
      <template #header>
        <NuxtLink to="/">
          <logoMed :tipo="0" />
        </NuxtLink>
      </template>

      <UNavigationMenu
        orientation="vertical"
        :items="navItems"
      />

      <template #footer>
        <div class="flex w-full flex-col gap-2">
          <div class="mb-2 flex flex-col gap-2 px-2">
            <UBadge
              :label="unidadeAtivaLabel"
              color="primary"
              variant="soft"
              class="w-full justify-center"
            />
            <UButton
              v-if="podeTrocarUnidade"
              icon="i-lucide-building-2"
              label="Trocar unidade"
              color="neutral"
              variant="ghost"
              class="w-full justify-start"
              @click="void (trocarUnidade())"
            />
            <UButton
              v-if="auth.isAdmin"
              icon="i-lucide-repeat"
              label="Trocar acesso"
              color="neutral"
              variant="ghost"
              class="w-full justify-start"
              @click="trocarAcesso()"
            />
          </div>
          <UButton
            icon="i-lucide-log-out"
            label="Sair"
            color="neutral"
            variant="ghost"
            class="w-full justify-start"
            :loading="verificandoLogout"
            @click="void tentarSair()"
          />
        </div>
      </template>
    </USidebar>

    <div class="flex min-h-dvh min-w-0 flex-1 flex-col">
      <UMain
        id="conteudo-principal"
        tabindex="-1"
        class="min-w-0"
      >
        <slot />
      </UMain>
    </div>

    <UModal
      v-model:open="modalLogoutBloqueadoAberto"
      :ui="{ content: 'max-h-[calc(100dvh-2rem)] overflow-y-auto' }"
    >
      <template #content>
        <div class="space-y-4 p-4 sm:p-6">
          <div class="flex min-w-0 items-start gap-2">
            <UIcon
              name="i-lucide-alert-triangle"
              class="mt-1 shrink-0 text-warning"
            />
            <h3 class="min-w-0 wrap-break-word text-xl font-black">
              Atendimento em andamento
            </h3>
          </div>
          <p
            class="wrap-break-word text-neutral-500 dark:text-neutral-400"
          >
            <template v-if="pacienteEmAtendimentoNome">
              Você possui um atendimento em andamento com
              <span class="font-semibold text-highlighted">{{ pacienteEmAtendimentoNome }}</span>.
            </template>
            <template v-else>
              Você possui um atendimento em andamento.
            </template>
            Finalize ou cancele o atendimento antes de sair do sistema.
          </p>
          <div class="grid grid-cols-1 gap-3 sm:grid-cols-2">
            <UButton
              label="Fechar"
              color="neutral"
              variant="ghost"
              block
              size="lg"
              class="font-bold rounded-xl"
              @click="fecharModalLogout"
            />
            <UButton
              label="Ir para o atendimento"
              icon="i-lucide-stethoscope"
              color="primary"
              variant="solid"
              block
              size="lg"
              class="font-bold rounded-xl"
              :loading="carregandoAtendimento"
              @click="void irParaAtendimento()"
            />
          </div>
        </div>
      </template>
    </UModal>
  </div>
</template>
