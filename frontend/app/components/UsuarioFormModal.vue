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
  >
    <template #header>
      <h2 class="text-lg font-semibold">
        {{ titulo }}
      </h2>
    </template>

    <template #body>
      <div class="space-y-4">
        <template v-if="role === 'medico'">
          <USeparator label="Vínculo SPDATA" />

          <div class="space-y-3">
            <div class="flex flex-col sm:flex-row gap-2">
              <UInput
                v-model="spdataBusca"
                class="flex-1"
                placeholder="Buscar médico por nome no SPDATA"
                :disabled="Boolean(usuario)"
                @keydown.enter.prevent="buscarSpdata"
              />
              <UButton
                label="Buscar SPDATA"
                :loading="buscandoSpdata"
                :disabled="Boolean(usuario) || !spdataBusca.trim()"
                @click="buscarSpdata"
              />
            </div>

            <div
              v-if="form.medico?.spdata_id"
              class="flex items-center gap-2 text-sm"
            >
              <UBadge
                :label="`SPDATA ID ${form.medico.spdata_id}`"
                color="success"
                variant="subtle"
              />
              <span class="text-muted">Médico vinculado ao SPDATA</span>
            </div>

            <div
              v-if="!usuario && usuariosStore.medicosSpdata.length"
              class="space-y-2 max-h-56 overflow-auto rounded-md border border-default p-2"
            >
              <button
                v-for="medico in usuariosStore.medicosSpdata"
                :key="medico.spdata_id"
                type="button"
                class="w-full text-left rounded-md border border-default p-3 hover:bg-muted/50 transition"
                @click="selecionarMedicoSpdata(medico)"
              >
                <p class="font-medium">
                  {{ medico.nome }}
                </p>
                <p class="text-xs text-muted">
                  ID {{ medico.spdata_id }} | CPF/CNPJ {{ medico.documento || '-' }} | CRM {{ medico.crm || '-' }}
                </p>
              </button>
            </div>
          </div>
        </template>

        <div class="flex flex-col gap-1">
          <label class="text-sm font-medium">Nome Completo</label>
          <UInput
            v-model="form.nome_completo"
            placeholder="Nome completo"
          />
        </div>

        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div class="flex flex-col gap-1">
            <label class="text-sm font-medium w-full">CPF/CNPJ</label>
            <UInput
              :model-value="form.cnpj_cpf"
              placeholder="000.000.000-00"
              @update:model-value="form.cnpj_cpf = formatarCpfCnpj($event)"
            />
          </div>
          <div class="flex flex-col gap-1">
            <label class="text-sm font-medium">Email</label>
            <UInput
              v-model="form.email"
              type="email"
              placeholder="email@exemplo.com"
            />
          </div>
        </div>

        <div class="flex flex-col gap-1">
          <label class="text-sm font-medium">
            Senha
          </label>
          <UInput
            v-model="form.senha"
            type="password"
            placeholder="Senha"
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
        </div>

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

          <USelectMenu
            v-else
            v-model="form.unidade_ids"
            :items="unidadesAtivas"
            value-key="id"
            label-key="nome"
            multiple
            placeholder="Selecione as unidades de atendimento"
            :search-input="{ placeholder: 'Buscar unidade...' }"
            class="w-full"
          />

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
            <div class="flex flex-col gap-1">
              <label class="text-sm font-medium">CRM</label>
              <UInput
                v-model="form.medico!.crm"
                placeholder="CRM"
              />
            </div>
            <div class="flex flex-col gap-1">
              <label class="text-sm font-medium">CRM UF</label>
              <UInputMenu
                v-model="form.medico!.crm_uf"
                :items="estadosBr"
                placeholder="UF"
              />
            </div>
            <div class="flex flex-col gap-1">
              <label class="text-sm font-medium">CRM Atendimento SPDATA</label>
              <UInput
                v-model="form.medico!.crm_atendimento_spdata"
                placeholder="CRM Atendimento"
              />
            </div>
            <div class="flex flex-col gap-1">
              <label class="text-sm font-medium">RQE</label>
              <UInput
                v-model="form.medico!.rqe"
                placeholder="RQE"
              />
            </div>
            <div class="flex flex-col gap-1 sm:col-span-2">
              <label class="text-sm font-medium">Especialidade</label>
              <UInput
                v-model="form.medico!.especialidade"
                placeholder="Especialidade"
              />
            </div>
          </div>
        </template>

        <div class="flex items-center gap-3">
          <USwitch v-model="form.ativo" />
          <label class="text-sm font-medium">Usuário ativo</label>
        </div>
      </div>
    </template>

    <template #footer>
      <div class="flex justify-end gap-2 w-full">
        <UButton
          label="Cancelar"
          color="neutral"
          variant="ghost"
          @click="void (open = false)"
        />
        <UButton
          label="Salvar"
          :loading="saving"
          :disabled="!podeSalvar"
          @click="salvar"
        />
      </div>
    </template>
  </UModal>
</template>
