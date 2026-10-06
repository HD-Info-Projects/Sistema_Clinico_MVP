<script setup lang="ts">
const auth = useAuthStore()
const agendamentosStore = useAgendamentosStore()
const toast = useToast()

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
const isAssistentePerfil = computed(() => auth.user?.role === 'assistente')
const chaveAtendimentoAtual = computed(() => (
  auth.user?.id && auth.activeClinicaId
    ? `${auth.user.id}:${auth.activeClinicaId}`
    : null
))
const atendimentoMenuDesabilitado = computed(() => (
  agendamentosStore.atendimentoAtualStatus === 'unknown'
  || agendamentosStore.atendimentoAtualStatus === 'loading'
  || agendamentosStore.atendimentoAtualStatus === 'absent'
))

async function abrirAtendimentoAtual() {
  const chave = chaveAtendimentoAtual.value
  if (!chave) return

  const resultado = await agendamentosStore.garantirAtendimentoAtual({
    chave,
    clinicaId: auth.activeClinicaId ?? undefined,
    medicoId: auth.user?.id
  })
  if (resultado.status === 'absent') {
    toast.add({
      title: 'Atendimento não disponível',
      description: 'Não há atendimento médico em andamento nesta unidade.',
      color: 'warning',
      icon: 'i-lucide-triangle-alert'
    })
    return
  }
  if (resultado.status === 'cancelled') return
  if (resultado.status !== 'present') {
    toast.add({
      title: 'Não foi possível verificar o atendimento',
      description: 'Verifique sua conexão e tente novamente.',
      color: 'error',
      icon: 'i-lucide-wifi-off'
    })
    return
  }

  await navigateTo('/atendimento-medico')
}

function trocarUnidade() {
  if (!isDesktop.value) open.value = false
  return navigateTo('/selecionar-clinica')
}

const navItems = computed(() => [
  ...(isAssistentePerfil.value
    ? [
        { label: 'Dashboard', icon: 'i-lucide-layout-dashboard', to: '/dashboard' }
      ]
    : []),
  ...(auth.isMedico
    ? [
        { label: 'Dashboard', icon: 'i-lucide-layout-dashboard', to: '/dashboard' },
        { label: 'Agenda', icon: 'i-lucide-calendar', to: '/agenda' },
        {
          label: 'Atendimento Médico',
          icon: 'i-lucide-stethoscope',
          disabled: atendimentoMenuDesabilitado.value,
          onSelect: () => void abrirAtendimentoAtual()
        },
        { label: 'Meus Pacientes', icon: 'i-lucide-users', to: '/pacientes' },
        { label: 'Padrões', icon: 'i-lucide-file-text', to: '/padroes-solicitacoes' }
      ]
    : []),
  ...(auth.canAccessLgpd
    ? [{ label: 'Auditoria LGPD', icon: 'i-lucide-shield-check', to: '/lgpd/auditoria' }]
    : [])
])

function trocarAcesso() {
  auth.limparAccessMode()
  navigateTo('/selecionar-acesso')
}

const verificandoLogout = ref(false)
const modalLogoutBloqueadoAberto = ref(false)
const pacienteEmAtendimentoNome = ref<string | null>(null)
const dataAtendimentoEmAndamento = ref<string | null>(null)
const erroVerificacaoLogout = ref(false)
const logoutRequestId = ref<string | null>(null)

async function tentarSair() {
  if (verificandoLogout.value) return
  erroVerificacaoLogout.value = false
  logoutRequestId.value = null
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
      pacienteEmAtendimentoNome.value = resultado.pacienteNome
      dataAtendimentoEmAndamento.value = resultado.data
      modalLogoutBloqueadoAberto.value = true
      return
    }

    if (!resultado.success && resultado.reason === 'verificacao') {
      erroVerificacaoLogout.value = true
      logoutRequestId.value = resultado.requestId
      modalLogoutBloqueadoAberto.value = true
      return
    }
  } finally {
    verificandoLogout.value = false
  }
}

async function irParaAtendimento() {
  modalLogoutBloqueadoAberto.value = false
  const chave = chaveAtendimentoAtual.value
  if (!chave) return

  await abrirAtendimentoAtual()
}

function revalidarAtendimentoAtual(force = false) {
  const chave = chaveAtendimentoAtual.value
  if (!chave || !auth.isMedico) return
  void agendamentosStore.verificarAtendimentoAtual(chave, force)
}

function revalidarAtendimentoAoFocar() {
  revalidarAtendimentoAtual(true)
}

watch(
  [() => auth.user?.id, () => auth.activeClinicaId, () => auth.isMedico],
  ([usuarioId, clinicaId, medico]) => {
    if (!import.meta.client) return
    if (!usuarioId || !clinicaId || !medico) {
      agendamentosStore.invalidarAtendimentoAtual()
      return
    }

    revalidarAtendimentoAtual()
  },
  { immediate: true }
)

onMounted(() => {
  window.addEventListener('focus', revalidarAtendimentoAoFocar)
})

onUnmounted(() => {
  window.removeEventListener('focus', revalidarAtendimentoAoFocar)
})

function fecharModalLogout() {
  modalLogoutBloqueadoAberto.value = false
  dataAtendimentoEmAndamento.value = null
  erroVerificacaoLogout.value = false
  logoutRequestId.value = null
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
              class="mt-1 shrink-0"
              :class="erroVerificacaoLogout ? 'text-error' : 'text-warning'"
            />
            <h3 class="min-w-0 wrap-break-word text-xl font-black">
              {{ erroVerificacaoLogout ? 'Verificação indisponível' : 'Atendimento em andamento' }}
            </h3>
          </div>
          <p
            v-if="erroVerificacaoLogout"
            class="wrap-break-word text-neutral-500 dark:text-neutral-400"
          >
            Não foi possível verificar se há atendimento em andamento. Tente novamente antes de sair.
            <span v-if="logoutRequestId">
              Código de referência:
              <span class="font-mono font-semibold text-highlighted">{{ logoutRequestId }}</span>.
            </span>
          </p>
          <p
            v-else
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
              v-if="erroVerificacaoLogout"
              label="Tentar novamente"
              icon="i-lucide-refresh-cw"
              color="primary"
              variant="solid"
              block
              size="lg"
              class="font-bold rounded-xl"
              @click="void tentarSair()"
            />
            <UButton
              v-else
              label="Ir para o atendimento"
              icon="i-lucide-stethoscope"
              color="primary"
              variant="solid"
              block
              size="lg"
              class="font-bold rounded-xl"
              @click="void irParaAtendimento()"
            />
          </div>
        </div>
      </template>
    </UModal>
  </div>
</template>
