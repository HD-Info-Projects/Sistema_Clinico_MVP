<script setup lang="ts">
import type { Usuario, UsuarioForm, RoleUsuario, MedicoSpdata } from '~/types'
import { formatarCpfCnpj } from '~/utils/masks'

const props = defineProps<{
  usuario?: Usuario | null
  role: RoleUsuario
}>()

const open = defineModel<boolean>('open', { default: false })
const emit = defineEmits<{ saved: [] }>()

const usuariosStore = useUsuariosStore()
const unidadesStore = useUnidadesStore()
const toast = useToast()

const form = ref<UsuarioForm>({
  nome_completo: '',
  cnpj_cpf: '',
  email: '',
  senha: '',
  role: props.role,
  ativo: true,
  unidade_ids: [],
  medico: props.role === 'medico' ? { ativo: true } : undefined
})

const saving = ref(false)
const buscandoSpdata = ref(false)
const spdataBusca = ref('')

const estadosBr = [
  'AC', 'AL', 'AP', 'AM', 'BA', 'CE', 'DF', 'ES', 'GO', 'MA',
  'MT', 'MS', 'MG', 'PA', 'PB', 'PR', 'PE', 'PI', 'RJ', 'RN',
  'RS', 'RO', 'RR', 'SC', 'SP', 'SE', 'TO'
]

const titulo = computed(() => {
  const acao = props.usuario ? 'Editar' : 'Novo'
  const tipo: Record<RoleUsuario, string> = {
    medico: 'Medico',
    recepcao: 'Recepcionista',
    admin: 'Administrador'
  }
  return `${acao} ${tipo[props.role]}`
})

const roleAtual = computed(() => form.value.role || props.role)
const exigeUnidade = computed(() => ['medico', 'recepcao'].includes(roleAtual.value))
const unidadesAtivas = computed(() => unidadesStore.unidades.filter(unidade => unidade.ativa !== false))
const unidadesSelecionadas = computed(() => form.value.unidade_ids ?? [])

const podeSalvar = computed(() => {
  const camposBase = Boolean(
    form.value.nome_completo.trim()
    && form.value.cnpj_cpf.trim()
    && form.value.email.trim()
  )
  const senhaValida = Boolean(props.usuario || (form.value.senha?.trim().length ?? 0) >= 8)
  const unidadesValidas = !exigeUnidade.value || unidadesSelecionadas.value.length > 0
  const medicoValido = roleAtual.value !== 'medico' || Boolean(form.value.medico?.spdata_id)

  return camposBase && senhaValida && unidadesValidas && medicoValido
})

watch(open, (isOpen) => {
  if (isOpen) {
    usuariosStore.limparMedicosSpdata()
    if (props.role !== 'admin' && unidadesStore.unidades.length === 0) {
      void unidadesStore.fetchAll()
    }
    form.value.role = props.role
    if (props.usuario) {
      form.value = {
        nome_completo: props.usuario.nome_completo,
        cnpj_cpf: formatarCpfCnpj(props.usuario.cnpj_cpf),
        email: props.usuario.email,
        senha: '',
        role: props.usuario.role,
        ativo: props.usuario.ativo ?? true,
        unidade_ids: props.usuario.unidade_ids ?? props.usuario.unidades?.map(unidade => unidade.id) ?? [],
        medico: props.usuario.role === 'medico'
          ? {
              spdata_id: props.usuario.medico?.spdata_id ?? null,
              crm: props.usuario.medico?.crm ?? '',
              crm_uf: props.usuario.medico?.crm_uf ?? '',
              crm_atendimento_spdata: props.usuario.medico?.crm_atendimento_spdata ?? '',
              rqe: props.usuario.medico?.rqe ?? '',
              especialidade: props.usuario.medico?.especialidade ?? '',
              ativo: props.usuario.medico?.ativo ?? true
            }
          : undefined
      }
      spdataBusca.value = props.usuario.nome_completo
    } else {
      form.value = {
        nome_completo: '',
        cnpj_cpf: '',
        email: '',
        senha: '',
        role: props.role,
        ativo: true,
        unidade_ids: [],
        medico: props.role === 'medico' ? { ativo: true } : undefined
      }
      spdataBusca.value = ''
    }
  }
})

async function buscarSpdata() {
  const nome = spdataBusca.value.trim()
  if (!nome) return

  buscandoSpdata.value = true
  try {
    const res = await usuariosStore.buscarMedicosSpdata({ nome })
    if (!res.success) {
      toast.add({ title: res.message, color: 'error' })
      return
    }
    if (res.data.length === 0) {
      toast.add({ title: 'Nenhum médico encontrado no SPDATA', color: 'warning' })
    }
  } finally {
    buscandoSpdata.value = false
  }
}

function selecionarMedicoSpdata(medico: MedicoSpdata) {
  form.value.nome_completo = medico.nome || ''
  form.value.cnpj_cpf = formatarCpfCnpj(medico.documento || '')
  if (!form.value.email && medico.email) form.value.email = medico.email
  form.value.medico = {
    ...form.value.medico,
    spdata_id: medico.spdata_id,
    crm: medico.crm || '',
    crm_uf: medico.crm_uf || '',
    crm_atendimento_spdata: medico.crm_atendimento_spdata || '',
    especialidade: medico.especialidade || '',
    ativo: true
  }
  spdataBusca.value = medico.nome
  toast.add({ title: 'Médico SPDATA selecionado', color: 'success' })
}

async function salvar() {
  if (!podeSalvar.value) return
  saving.value = true
  try {
    const dados = { ...form.value, medico: form.value.medico ? { ...form.value.medico } : undefined }
    dados.cnpj_cpf = dados.cnpj_cpf.replace(/\D/g, '')
    if (!dados.senha?.trim()) delete dados.senha
    if (!exigeUnidade.value) delete dados.unidade_ids

    if (props.usuario) {
      const res = await usuariosStore.atualizar(props.usuario.id, dados)
      if (res.success) {
        toast.add({ title: res.message, color: 'success' })
        open.value = false
        emit('saved')
      } else {
        toast.add({ title: res.message, color: 'error' })
      }
    } else {
      const res = await usuariosStore.criar(dados)
      if (res.success) {
        toast.add({ title: res.message, color: 'success' })
        open.value = false
        emit('saved')
      } else {
        toast.add({ title: res.message, color: 'error' })
      }
    }
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <UModal
    v-model:open="open"
    :ui="{
      content: 'max-h-[calc(100dvh-2rem)]',
      header: 'shrink-0',
      body: 'overflow-y-auto',
      footer: 'shrink-0'
    }"
  >
    <template #header>
      <h2 class="min-w-0 break-words text-lg font-semibold">
        {{ titulo }}
      </h2>
    </template>

    <template #body>
      <div class="space-y-4">
        <template v-if="role === 'medico'">
          <USeparator label="Vínculo SPDATA" />

          <div class="space-y-3">
            <div class="flex flex-col gap-2 sm:flex-row sm:items-end">
              <UFormField
                label="Médico no SPDATA"
                class="min-w-0 flex-1"
              >
                <UInput
                  v-model="spdataBusca"
                  class="w-full"
                  placeholder="Buscar médico por nome no SPDATA"
                  :disabled="Boolean(usuario)"
                  @keydown.enter.prevent="buscarSpdata"
                />
              </UFormField>
              <UButton
                label="Buscar SPDATA"
                class="w-full justify-center sm:w-auto"
                :loading="buscandoSpdata"
                :disabled="Boolean(usuario) || !spdataBusca.trim()"
                @click="buscarSpdata"
              />
            </div>

            <div
              v-if="form.medico?.spdata_id"
              class="flex min-w-0 flex-wrap items-center gap-2 text-sm"
            >
              <UBadge
                :label="`SPDATA ID ${form.medico.spdata_id}`"
                color="success"
                variant="subtle"
              />
              <span class="min-w-0 break-words text-muted">Médico vinculado ao SPDATA</span>
            </div>

            <div
              v-if="!usuario && usuariosStore.medicosSpdata.length"
              class="space-y-2 max-h-56 overflow-auto rounded-md border border-default p-2"
            >
              <button
                v-for="medico in usuariosStore.medicosSpdata"
                :key="medico.spdata_id"
                type="button"
                class="min-h-11 w-full min-w-0 rounded-md border border-default p-3 text-left transition hover:bg-muted/50"
                @click="selecionarMedicoSpdata(medico)"
              >
                <p class="break-words font-medium">
                  {{ medico.nome }}
                </p>
                <p class="break-words text-xs text-muted">
                  ID {{ medico.spdata_id }} | CPF/CNPJ {{ medico.documento || '-' }} | CRM {{ medico.crm || '-' }}
                </p>
              </button>
            </div>
          </div>
        </template>

        <UFormField label="Nome Completo">
          <UInput
            v-model="form.nome_completo"
            placeholder="Nome completo"
            class="w-full"
          />
        </UFormField>

        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <UFormField label="CPF/CNPJ">
            <UInput
              :model-value="form.cnpj_cpf"
              placeholder="000.000.000-00"
              class="w-full"
              @update:model-value="form.cnpj_cpf = formatarCpfCnpj($event)"
            />
          </UFormField>
          <UFormField label="Email">
            <UInput
              v-model="form.email"
              type="email"
              placeholder="email@exemplo.com"
              class="w-full"
            />
          </UFormField>
        </div>

        <UFormField label="Senha">
          <UInput
            v-model="form.senha"
            type="password"
            placeholder="Senha"
            class="w-full"
          />
          <p
            v-if="usuario"
            class="text-xs text-muted"
          >
            Deixe vazio para manter a senha atual.
          </p>
          <p
            v-if="!usuario && (form.senha?.trim().length ?? 0) > 0 && (form.senha?.trim().length ?? 0) < 8"
            class="text-xs text-error"
          >
            A senha deve ter pelo menos 8 caracteres.
          </p>
        </UFormField>

        <template v-if="exigeUnidade">
          <USeparator label="Unidades de atendimento" />

          <div
            v-if="unidadesStore.loading"
            class="flex items-center gap-2 text-sm text-muted"
          >
            <UIcon
              name="i-lucide-loader-circle"
              class="animate-spin"
            />
            Carregando unidades...
          </div>

          <UAlert
            v-else-if="unidadesStore.error"
            :title="unidadesStore.error || 'Erro ao carregar unidades'"
            color="error"
            variant="subtle"
            icon="i-lucide-circle-alert"
          />

          <UAlert
            v-else-if="unidadesAtivas.length === 0"
            title="Nenhuma unidade ativa cadastrada"
            description="Cadastre uma unidade ativa antes de criar médicos ou recepcionistas."
            color="warning"
            variant="subtle"
            icon="i-lucide-building"
          />

          <UFormField
            v-else
            label="Unidades de atendimento"
          >
            <USelectMenu
              v-model="form.unidade_ids"
              :items="unidadesAtivas"
              value-key="id"
              label-key="nome"
              multiple
              placeholder="Selecione as unidades de atendimento"
              :search-input="{ placeholder: 'Buscar unidade...' }"
              class="w-full"
            />
          </UFormField>

          <p
            v-if="unidadesAtivas.length > 0 && unidadesSelecionadas.length === 0"
            class="text-xs text-error"
          >
            Selecione ao menos uma unidade.
          </p>
        </template>

        <template v-if="role === 'medico'">
          <USeparator label="Dados Médicos" />

          <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <UFormField label="CRM">
              <UInput
                v-model="form.medico!.crm"
                placeholder="CRM"
                class="w-full"
              />
            </UFormField>
            <UFormField label="CRM UF">
              <UInputMenu
                v-model="form.medico!.crm_uf"
                :items="estadosBr"
                placeholder="UF"
                class="w-full"
              />
            </UFormField>
            <UFormField label="CRM Atendimento SPDATA">
              <UInput
                v-model="form.medico!.crm_atendimento_spdata"
                placeholder="CRM Atendimento"
                class="w-full"
              />
            </UFormField>
            <UFormField label="RQE">
              <UInput
                v-model="form.medico!.rqe"
                placeholder="RQE"
                class="w-full"
              />
            </UFormField>
            <UFormField
              label="Especialidade"
              class="sm:col-span-2"
            >
              <UInput
                v-model="form.medico!.especialidade"
                placeholder="Especialidade"
                class="w-full"
              />
            </UFormField>
          </div>
        </template>

        <div class="flex items-center gap-3">
          <USwitch
            id="usuario-ativo"
            v-model="form.ativo"
          />
          <label
            for="usuario-ativo"
            class="text-sm font-medium"
          >Usuário ativo</label>
        </div>
      </div>
    </template>

    <template #footer>
      <div class="flex w-full flex-col-reverse gap-2 sm:flex-row sm:justify-end">
        <UButton
          label="Cancelar"
          color="neutral"
          variant="ghost"
          class="w-full justify-center sm:w-auto"
          @click="void (open = false)"
        />
        <UButton
          label="Salvar"
          :loading="saving"
          :disabled="!podeSalvar"
          class="w-full justify-center sm:w-auto"
          @click="salvar"
        />
      </div>
    </template>
  </UModal>
</template>
