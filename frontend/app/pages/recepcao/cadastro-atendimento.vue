<script setup lang="ts">
import { CalendarDate } from '@internationalized/date'

interface PacienteRecepcao {
  idPacienteSpdata: number
  prontuario?: string
  nome: string
  nomeSocial?: string | null
  cpf?: string
  dataNascimento?: string | null
}

interface MedicoRecepcao {
  id: number
  nome: string
  spdataId?: number | null
  crm?: string | null
  crmAtendimento?: string | null
  especialidade?: string | null
}

interface ConvenioRecepcao {
  idConvenioSpdata: number
  nome: string
}

interface ProcedimentoRecepcao {
  id: number
  spdataTpId: number
  nome: string
  codigoProcedimento?: number | null
  codigoTuss?: number | null
}

const auth = useAuthStore()
const route = useRoute()
const toast = useToast()

const hoje = new Date()
const userName = computed(() => auth.user?.nome || 'Usuário')
const dataAtendimento = shallowRef<CalendarDate | null>(new CalendarDate(hoje.getFullYear(), hoje.getMonth() + 1, hoje.getDate()))

const buscaPaciente = ref('')
const pacientes = ref<PacienteRecepcao[]>([])
const medicos = ref<MedicoRecepcao[]>([])
const convenios = ref<ConvenioRecepcao[]>([])
const procedimentos = ref<ProcedimentoRecepcao[]>([])
const buscandoPaciente = ref(false)
const carregandoOpcoes = ref(true)
const salvando = ref(false)

const form = reactive({
  idPacienteSpdata: undefined as number | undefined,
  medicoId: undefined as number | undefined,
  idConvenioSpdata: undefined as number | undefined,
  procedimentoId: undefined as number | undefined,
  horario: '',
  observacao: ''
})

const pacienteSelecionado = computed(() => pacientes.value.find(p => p.idPacienteSpdata === form.idPacienteSpdata) ?? null)
const medicoSelecionado = computed(() => medicos.value.find(m => m.id === form.medicoId) ?? null)
const procedimentoSelecionado = computed(() => procedimentos.value.find(p => p.id === form.procedimentoId) ?? null)

const pacientesItems = computed(() => pacientes.value.map(paciente => ({
  label: `${paciente.nome}${paciente.cpf ? ` - CPF ${paciente.cpf}` : ''}${paciente.prontuario ? ` - pront. ${paciente.prontuario}` : ''}`,
  value: paciente.idPacienteSpdata
})))

const medicosItems = computed(() => medicos.value.map(medico => ({
  label: `${medico.nome}${medico.crmAtendimento || medico.crm ? ` - CRM ${medico.crmAtendimento || medico.crm}` : ''}`,
  value: medico.id
})))

const conveniosItems = computed(() => convenios.value.map(convenio => ({
  label: convenio.nome,
  value: convenio.idConvenioSpdata
})))

const procedimentosItems = computed(() => procedimentos.value.map(procedimento => ({
  label: `${procedimento.nome}${procedimento.codigoTuss ? ` - TUSS ${procedimento.codigoTuss}` : ''}`,
  value: procedimento.id
})))

function mensagemErro(error: unknown, fallback: string) {
  const err = error as { data?: { error?: string, message?: string }, message?: string }
  return err.data?.error || err.data?.message || err.message || fallback
}

function dataCalendarIso(data: CalendarDate | null) {
  if (!data) return null
  return `${data.year}-${String(data.month).padStart(2, '0')}-${String(data.day).padStart(2, '0')}`
}

function textoInformado(valor: string | number | null | undefined, fallback = 'Não informado') {
  const texto = String(valor ?? '').trim()
  return texto || fallback
}

async function buscarPacientes() {
  const termo = buscaPaciente.value.trim()
  if (termo.length < 2) {
    toast.add({ title: 'Digite ao menos 2 caracteres para buscar o paciente.', color: 'error' })
    return
  }

  buscandoPaciente.value = true
  try {
    const response = await $fetch<{ pacientes: PacienteRecepcao[] }>(`/api/recepcao/pacientes/buscar?q=${encodeURIComponent(termo)}`)
    pacientes.value = response.pacientes ?? []
    if (pacientes.value.length === 1) form.idPacienteSpdata = pacientes.value[0]!.idPacienteSpdata
    if (!pacientes.value.length) toast.add({ title: 'Nenhum paciente encontrado no SPDATA.', color: 'warning' })
  } catch (error) {
    toast.add({ title: mensagemErro(error, 'Não foi possível buscar pacientes.'), color: 'error' })
  } finally {
    buscandoPaciente.value = false
  }
}

async function carregarPacienteInicial() {
  const pacienteId = Number(route.query.pacienteId)
  if (!pacienteId || Number.isNaN(pacienteId)) return

  try {
    const response = await $fetch<{ pacientes: PacienteRecepcao[] }>(`/api/recepcao/pacientes/buscar?id=${pacienteId}`)
    pacientes.value = response.pacientes ?? []
    if (pacientes.value.length) {
      form.idPacienteSpdata = pacientes.value[0]!.idPacienteSpdata
      buscaPaciente.value = pacientes.value[0]!.nome
    }
  } catch (error) {
    toast.add({ title: mensagemErro(error, 'Não foi possível carregar o paciente selecionado.'), color: 'error' })
  }
}

async function carregarOpcoes() {
  carregandoOpcoes.value = true
  try {
    const [medicosResponse, conveniosResponse, procedimentosResponse] = await Promise.all([
      $fetch<{ medicos: MedicoRecepcao[] }>('/api/recepcao/medicos'),
      $fetch<{ convenios: ConvenioRecepcao[] }>('/api/recepcao/convenios'),
      $fetch<{ procedimentos: ProcedimentoRecepcao[] }>('/api/recepcao/procedimentos')
    ])
    medicos.value = medicosResponse.medicos ?? []
    convenios.value = conveniosResponse.convenios ?? []
    procedimentos.value = procedimentosResponse.procedimentos ?? []
  } catch (error) {
    toast.add({ title: mensagemErro(error, 'Não foi possível carregar dados do atendimento.'), color: 'error' })
  } finally {
    carregandoOpcoes.value = false
  }
}

function validarFormulario() {
  if (!auth.activeClinicaId) return 'Selecione uma unidade antes de cadastrar atendimento.'
  if (!form.idPacienteSpdata) return 'Selecione um paciente.'
  if (!form.medicoId) return 'Selecione um médico.'
  if (!form.idConvenioSpdata) return 'Selecione um convênio.'
  if (!form.procedimentoId) return 'Selecione um procedimento.'
  if (!dataAtendimento.value) return 'Informe a data do atendimento.'
  if (!form.horario) return 'Informe o horário do atendimento.'
  return null
}

async function salvarAtendimento() {
  const erro = validarFormulario()
  if (erro) {
    toast.add({ title: erro, color: 'error' })
    return
  }

  salvando.value = true
  try {
    const response = await $fetch<{ created: boolean }>('/api/recepcao/atendimentos', {
      method: 'POST',
      body: {
        idPacienteSpdata: form.idPacienteSpdata,
        medicoId: form.medicoId,
        idConvenioSpdata: form.idConvenioSpdata,
        procedimentoId: form.procedimentoId,
        procedimentoIdSpdata: procedimentoSelecionado.value?.spdataTpId,
        data: dataCalendarIso(dataAtendimento.value),
        horario: form.horario,
        observacao: form.observacao
      }
    })

    toast.add({
      title: response.created ? 'Atendimento criado no SPDATA.' : 'Atendimento já existia no SPDATA.',
      description: 'Ele aparecerá como em espera na recepção e na agenda médica.',
      color: 'success'
    })
    await navigateTo('/recepcao/agenda')
  } catch (error) {
    toast.add({ title: mensagemErro(error, 'Não foi possível salvar o atendimento.'), color: 'error' })
  } finally {
    salvando.value = false
  }
}

onMounted(async () => {
  await Promise.all([carregarOpcoes(), carregarPacienteInicial()])
})
</script>

<template>
  <div>
    <UHeader title="Cadastro de Atendimento">
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

    <div class="min-h-[calc(100vh-var(--ui-header-height))] bg-muted p-4 sm:p-6 sm:py-4">
      <div class="mx-auto flex max-w-6xl flex-col gap-4">
        <UAlert
          icon="i-lucide-info"
          color="primary"
          variant="soft"
          title="O atendimento será criado no SPDATA"
          description="Depois da gravação, o MedSystem busca o atendimento de volta e exibe o paciente como em espera para recepção e médico."
        />

        <CardCadastro
          titulo="Paciente"
          cor="primary"
          icone="i-lucide-user-search"
        >
          <div class="grid gap-4 lg:grid-cols-[minmax(0,1fr)_auto]">
            <UFormField
              label="Buscar por nome, CPF ou prontuário"
              name="buscaPaciente"
            >
              <UInput
                v-model="buscaPaciente"
                placeholder="Digite os dados do paciente"
                class="w-full"
                @keyup.enter="buscarPacientes"
              />
            </UFormField>

            <div class="flex items-end">
              <UButton
                label="Buscar paciente"
                icon="i-lucide-search"
                :loading="buscandoPaciente"
                class="w-full lg:w-auto"
                @click="buscarPacientes"
              />
            </div>
          </div>

          <div class="mt-4 grid gap-4 lg:grid-cols-[minmax(0,1fr)_auto]">
            <UFormField
              label="Paciente selecionado"
              name="idPacienteSpdata"
            >
              <USelect
                v-model="form.idPacienteSpdata"
                :items="pacientesItems"
                placeholder="Selecione um paciente"
                class="w-full"
              />
            </UFormField>

            <div class="flex items-end">
              <UButton
                label="Novo paciente"
                icon="i-lucide-user-plus"
                color="neutral"
                variant="outline"
                to="/recepcao/cadastro-pacientes"
                class="w-full lg:w-auto"
              />
            </div>
          </div>

          <div
            v-if="pacienteSelecionado"
            class="mt-4 grid gap-3 rounded-lg border border-default bg-default p-4 text-sm sm:grid-cols-3"
          >
            <div>
              <p class="text-muted">
                Nome
              </p>
              <p class="font-medium">
                {{ pacienteSelecionado.nome }}
              </p>
            </div>
            <div>
              <p class="text-muted">
                CPF
              </p>
              <p class="font-medium">
                {{ textoInformado(pacienteSelecionado.cpf) }}
              </p>
            </div>
            <div>
              <p class="text-muted">
                Prontuário
              </p>
              <p class="font-medium">
                {{ textoInformado(pacienteSelecionado.prontuario) }}
              </p>
            </div>
          </div>
        </CardCadastro>

        <CardCadastro
          titulo="Dados do Atendimento"
          cor="tertiary"
          icone="i-lucide-user-check"
        >
          <div class="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
            <UFormField
              label="Médico"
              name="medicoId"
            >
              <USelect
                v-model="form.medicoId"
                :items="medicosItems"
                :loading="carregandoOpcoes"
                placeholder="Selecione o médico"
                class="w-full"
              />
            </UFormField>

            <UFormField
              label="Convênio"
              name="idConvenioSpdata"
            >
              <USelect
                v-model="form.idConvenioSpdata"
                :items="conveniosItems"
                :loading="carregandoOpcoes"
                placeholder="Selecione o convênio"
                class="w-full"
              />
            </UFormField>

            <UFormField
              label="Data"
              name="data"
            >
              <UInputDate
                v-model="dataAtendimento"
                class="w-full"
              />
            </UFormField>

            <UFormField
              label="Horário"
              name="horario"
            >
              <UInput
                v-model="form.horario"
                type="time"
                class="w-full"
              />
            </UFormField>
          </div>

          <div class="mt-4 grid gap-4 lg:grid-cols-[minmax(0,1fr)_minmax(16rem,24rem)]">
            <UFormField
              label="Procedimento"
              name="procedimentoId"
            >
              <USelect
                v-model="form.procedimentoId"
                :items="procedimentosItems"
                :loading="carregandoOpcoes"
                placeholder="Selecione o procedimento"
                class="w-full"
              />
            </UFormField>

            <div
              v-if="medicoSelecionado"
              class="rounded-lg border border-default bg-default p-3 text-sm"
            >
              <p class="text-muted">
                Médico selecionado
              </p>
              <p class="font-medium">
                {{ medicoSelecionado.nome }}
              </p>
              <p class="text-muted">
                {{ textoInformado(medicoSelecionado.especialidade, 'Especialidade não informada') }}
              </p>
            </div>
          </div>

          <UFormField
            label="Observação"
            name="observacao"
            class="mt-4"
          >
            <UTextarea
              v-model="form.observacao"
              placeholder="Informações complementares para o atendimento"
              :rows="4"
              class="w-full"
            />
          </UFormField>
        </CardCadastro>

        <div class="flex flex-col gap-3 rounded-xl border border-default bg-default p-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <p class="font-medium">
              Status após salvar: em espera
            </p>
            <p class="text-sm text-muted">
              O MedSystem não cria atendimento local solto; ele sincroniza o atendimento criado no SPDATA.
            </p>
          </div>
          <UButton
            label="Criar atendimento"
            icon="i-lucide-circle-check"
            size="lg"
            :loading="salvando"
            :disabled="salvando || carregandoOpcoes"
            class="w-full sm:w-auto"
            @click="salvarAtendimento"
          />
        </div>
      </div>
    </div>
  </div>
</template>
