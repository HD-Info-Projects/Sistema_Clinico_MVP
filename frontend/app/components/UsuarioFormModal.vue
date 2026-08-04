<script setup lang="ts">
import type { Usuario, UsuarioForm, RoleUsuario } from '~/types'

const props = defineProps<{
  usuario?: Usuario | null
  role: RoleUsuario
}>()

const open = defineModel<boolean>('open', { default: false })
const emit = defineEmits<{ saved: [] }>()

const usuariosStore = useUsuariosStore()
const toast = useToast()

const form = ref<UsuarioForm>({
  nome_completo: '',
  cnpj_cpf: '',
  email: '',
  senha: '',
  role: props.role,
  medico: props.role === 'medico' ? {} : undefined
})

const saving = ref(false)

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

watch(open, (isOpen) => {
  if (isOpen) {
    form.value.role = props.role
    if (props.usuario) {
      form.value = {
        nome_completo: props.usuario.nome_completo,
        cnpj_cpf: props.usuario.cnpj_cpf,
        email: props.usuario.email,
        senha: '',
        role: props.usuario.role,
        medico: props.usuario.role === 'medico'
          ? {
              crm: props.usuario.medico?.crm ?? '',
              crm_uf: props.usuario.medico?.crm_uf ?? '',
              crm_atendimento_spdata: props.usuario.medico?.crm_atendimento_spdata ?? '',
              rqe: props.usuario.medico?.rqe ?? '',
              especialidade: props.usuario.medico?.especialidade ?? ''
            }
          : undefined
      }
    } else {
      form.value = {
        nome_completo: '',
        cnpj_cpf: '',
        email: '',
        senha: '',
        role: props.role,
        medico: props.role === 'medico' ? {} : undefined
      }
    }
  }
})

async function salvar() {
  if (!form.value.nome_completo.trim() || !form.value.email.trim()) return
  saving.value = true
  try {
    const dados = { ...form.value }
    if (!dados.senha?.trim()) delete dados.senha

    if (props.usuario) {
      const res = await usuariosStore.atualizar(props.usuario.id, dados)
      if (res.success) {
        toast.add({ title: 'Usuario atualizado', color: 'success' })
        open.value = false
        emit('saved')
      } else {
        toast.add({ title: res.message, color: 'error' })
      }
    } else {
      const res = await usuariosStore.criar(dados)
      if (res.success) {
        toast.add({ title: 'Usuario criado', color: 'success' })
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
        <div class="space-y-1">
          <label class="text-sm font-medium">Nome Completo</label>
          <UInput
            v-model="form.nome_completo"
            placeholder="Nome completo"
          />
        </div>

        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div class="space-y-1">
            <label class="text-sm font-medium">CPF</label>
            <UInput
              v-model="form.cnpj_cpf"
              placeholder="000.000.000-00"
            />
          </div>
          <div class="space-y-1">
            <label class="text-sm font-medium">Email</label>
            <UInput
              v-model="form.email"
              type="email"
              placeholder="email@exemplo.com"
            />
          </div>
        </div>

        <div class="space-y-1">
          <label class="text-sm font-medium">
            Senha {{ usuario ? '(deixe vazio para manter)' : '' }}
          </label>
          <UInput
            v-model="form.senha"
            type="password"
            placeholder="Senha"
          />
        </div>

        <template v-if="role === 'medico'">
          <USeparator label="Dados Medicos" />

          <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div class="space-y-1">
              <label class="text-sm font-medium">CRM</label>
              <UInput
                v-model="form.medico!.crm"
                placeholder="CRM"
              />
            </div>
            <div class="space-y-1">
              <label class="text-sm font-medium">CRM UF</label>
              <UInputMenu
                v-model="form.medico!.crm_uf"
                :items="estadosBr"
                placeholder="UF"
              />
            </div>
          </div>

          <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div class="space-y-1">
              <label class="text-sm font-medium">CRM Atendimento SPDATA</label>
              <UInput
                v-model="form.medico!.crm_atendimento_spdata"
                placeholder="CRM Atendimento"
              />
            </div>
            <div class="space-y-1">
              <label class="text-sm font-medium">RQE</label>
              <UInput
                v-model="form.medico!.rqe"
                placeholder="RQE"
              />
            </div>
          </div>

          <div class="space-y-1">
            <label class="text-sm font-medium">Especialidade</label>
            <UInput
              v-model="form.medico!.especialidade"
              placeholder="Especialidade"
            />
          </div>
        </template>
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
          :disabled="!form.nome_completo.trim() || !form.email.trim()"
          @click="salvar"
        />
      </div>
    </template>
  </UModal>
</template>
