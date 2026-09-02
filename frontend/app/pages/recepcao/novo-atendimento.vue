<script setup lang="ts">
import { CalendarDate, type Time } from '@internationalized/date'
import { formatarCpf, formatarCpfCnpj, formatarTelefone } from '~/utils/masks'

type PacienteMock = {
  nome: string
  cpf: string
  prontuario: string
  dataNascimento: string
  sexoBiologico: string
  cidade: string
  celularWhatsapp: string
  email: string
  logradouro: string
  bairro: string
  estadoUf: string
}

type EnderecoViaCep = { erro?: boolean, logradouro?: string, complemento?: string, bairro?: string, localidade?: string, uf?: string, ibge?: string }

const auth = useAuthStore()
const toast = useToast()
const userName = computed(() => auth.user?.nome || 'Usuário')
const tabAtiva = ref('paciente')
const pacienteConcluido = ref(false)
const atendimentoConcluido = ref(false)
const pacienteSelecionado = ref<PacienteMock | null>(null)
const fotoPaciente = ref<File | null>(null)
const fotoPacienteUrl = ref<string | null>(null)
const dataNascimento = shallowRef<CalendarDate | null>(null)
const dataEntrada = shallowRef<CalendarDate | null>(null)
const horaEntrada = shallowRef<Time | null>(null)
const dataNascimentoResponsavel = shallowRef<CalendarDate | null>(null)
const cepBuscando = ref(false)
const cepErro = ref('')
const cameraAberta = ref(false)
const cameraCarregando = ref(false)
const cameraErro = ref('')
const videoCamera = ref<HTMLVideoElement | null>(null)
let streamCamera: MediaStream | null = null
let consultaCepTimer: ReturnType<typeof setTimeout> | null = null
let consultaCepAtual = 0
let proximoProntuario = 1000
const prontuarioNovo = ref('')

const paciente = reactive({
  nomeCompleto: '', nomeSocial: '', cpf: '', nomeMae: '', rg: '', orgaoEmissor: '', sexoBiologico: '', identidadeGenero: '', estadoCivil: '', nacionalidade: '', naturalidade: '', celularWhatsapp: '', telefoneFixo: '', email: '', cep: '', logradouro: '', numero: '', complemento: '', bairro: '', cidade: '', estadoUf: '', codigoIbge: ''
})
const atendimento = reactive({
  registro: '', caraterSolicitacao: '', codigoProcedimento: '', nomeProcedimento: '', tipoProcedimento: '', modalidade: '', ehRetorno: false, recemNascido: false, atualizaFaturamento: false, numeroConvenio: '', descricaoConvenio: '', matricula: '', validade: '', guiaAutorizacao: '', crm: '', nomeMedico: '', especialidade: '', centroCustoNumero: '', centroCustoNome: '', unidade: ''
})
const responsavel = reactive({
  nome: '', identidade: '', cpf: '', cnpj: '', parentesco: '', cep: '', logradouro: '', numero: '', complemento: '', bairro: '', cidade: '', uf: '', telefone: '', profissao: ''
})

const pacientesMockados: PacienteMock[] = [
  { nome: 'Ana Beatriz Souza', cpf: '123.456.789-09', prontuario: 'PR-000123', dataNascimento: '1992-06-18', sexoBiologico: 'feminino', cidade: 'Belo Horizonte', celularWhatsapp: '(31) 99999-1111', email: 'ana.souza@exemplo.com', logradouro: 'Rua da Bahia', bairro: 'Centro', estadoUf: 'MG' },
  { nome: 'Carlos Eduardo Lima', cpf: '987.654.321-00', prontuario: 'PR-000456', dataNascimento: '1985-11-04', sexoBiologico: 'masculino', cidade: 'Contagem', celularWhatsapp: '(31) 98888-2222', email: 'carlos.lima@exemplo.com', logradouro: 'Avenida João César', bairro: 'Eldorado', estadoUf: 'MG' }
]
const opcoesSexo = [{ label: 'Masculino', value: 'masculino' }, { label: 'Feminino', value: 'feminino' }, { label: 'Intersexo', value: 'intersexo' }, { label: 'Prefiro não informar', value: 'nao_informar' }]
const opcoesGenero = [{ label: 'Mulher cisgênero', value: 'mulher_cisgenero' }, { label: 'Homem cisgênero', value: 'homem_cisgenero' }, { label: 'Mulher transgênero', value: 'mulher_transgenero' }, { label: 'Homem transgênero', value: 'homem_transgenero' }, { label: 'Não binário', value: 'nao_binario' }, { label: 'Outra', value: 'outra' }, { label: 'Prefiro não informar', value: 'nao_informar' }]
const opcoesEstadoCivil = ['Solteiro(a)', 'Casado(a)', 'União estável', 'Divorciado(a)', 'Viúvo(a)', 'Prefiro não informar']
const estadosBr = ['AC', 'AL', 'AP', 'AM', 'BA', 'CE', 'DF', 'ES', 'GO', 'MA', 'MT', 'MS', 'MG', 'PA', 'PB', 'PR', 'PE', 'PI', 'RJ', 'RN', 'RS', 'RO', 'RR', 'SC', 'SP', 'SE', 'TO']
const opcoesCarater = ['Eletiva', 'Urgência', 'Emergência']
const opcoesTipo = ['Consulta', 'Exame', 'Procedimento', 'Terapia']
const opcoesModalidade = ['Ambulatorial', 'Hospitalar', 'Domiciliar', 'Teleatendimento']

const tabItems = computed(() => [
  { label: 'Paciente', value: 'paciente', icon: 'i-lucide-user-round', slot: 'paciente' },
  { label: 'Atendimento', value: 'atendimento', icon: 'i-lucide-stethoscope', slot: 'atendimento', disabled: !pacienteConcluido.value },
  { label: 'Responsável', value: 'responsavel', icon: 'i-lucide-users', slot: 'responsavel', disabled: !atendimentoConcluido.value }
])
const sugestoesPacientes = computed(() => pacientesMockados.map(p => ({ label: p.nome, cpf: p.cpf, prontuario: p.prontuario, onSelect: () => selecionarPaciente(p) })))
const prontuarioAtual = computed(() => pacienteSelecionado.value?.prontuario || prontuarioNovo.value || 'Será gerado ao avançar')
const idadePaciente = computed(() => {
  const data = dataNascimento.value
  const nasc = pacienteSelecionado.value
    ? new Date(`${pacienteSelecionado.value.dataNascimento}T12:00:00`)
    : data ? new Date(`${data.year}-${String(data.month).padStart(2, '0')}-${String(data.day).padStart(2, '0')}T12:00:00`) : null
  if (!nasc) return ''
  const hoje = new Date()
  let idade = hoje.getFullYear() - nasc.getFullYear()
  if (hoje.getMonth() < nasc.getMonth() || (hoje.getMonth() === nasc.getMonth() && hoje.getDate() < nasc.getDate())) idade--
  return `${idade} anos`
})

function limparEtapasSeguintes() {
  Object.assign(atendimento, { registro: '', caraterSolicitacao: '', codigoProcedimento: '', nomeProcedimento: '', tipoProcedimento: '', modalidade: '', ehRetorno: false, recemNascido: false, atualizaFaturamento: false, numeroConvenio: '', descricaoConvenio: '', matricula: '', validade: '', guiaAutorizacao: '', crm: '', nomeMedico: '', especialidade: '', centroCustoNumero: '', centroCustoNome: '', unidade: '' })
  Object.assign(responsavel, { nome: '', identidade: '', cpf: '', cnpj: '', parentesco: '', cep: '', logradouro: '', numero: '', complemento: '', bairro: '', cidade: '', uf: '', telefone: '', profissao: '' })
  dataEntrada.value = null
  horaEntrada.value = null
  dataNascimentoResponsavel.value = null
  atendimentoConcluido.value = false
}

function selecionarPaciente(item: PacienteMock) {
  pacienteSelecionado.value = item
  const [ano, mes, dia] = item.dataNascimento.split('-').map(Number)
  dataNascimento.value = new CalendarDate(ano!, mes!, dia!)
  prontuarioNovo.value = ''
  Object.assign(paciente, { nomeCompleto: item.nome, cpf: item.cpf, sexoBiologico: item.sexoBiologico, cidade: item.cidade, celularWhatsapp: item.celularWhatsapp, email: item.email, logradouro: item.logradouro, bairro: item.bairro, estadoUf: item.estadoUf })
  limparEtapasSeguintes()
}

function iniciarPacienteNovo() {
  if (!pacienteSelecionado.value) return
  pacienteSelecionado.value = null
  prontuarioNovo.value = ''
  limparEtapasSeguintes()
}

function proximoPaciente() {
  if (!paciente.nomeCompleto.trim()) {
    toast.add({ title: 'Informe o nome completo do paciente.', color: 'error' })
    return
  }
  if (!pacienteSelecionado.value && !prontuarioNovo.value) {
    prontuarioNovo.value = `PR-NOVO-${proximoProntuario++}`
  }
  pacienteConcluido.value = true
  tabAtiva.value = 'atendimento'
  toast.add({ title: 'Dados do paciente guardados nesta sessão.', color: 'success' })
}

function proximoAtendimento() {
  atendimentoConcluido.value = true
  tabAtiva.value = 'responsavel'
}

function finalizarCadastro() {
  toast.add({ title: 'Cadastro concluído nesta sessão.', description: 'Nenhum dado foi enviado ao sistema ainda.', color: 'success' })
}

function formatarCep(valor: string) {
  const digitos = valor.replace(/\D/g, '').slice(0, 8)
  return digitos.length > 5 ? `${digitos.slice(0, 5)}-${digitos.slice(5)}` : digitos
}

async function buscarEnderecoPorCep(cep: string, consulta: number) {
  cepBuscando.value = true
  cepErro.value = ''
  try {
    const endereco = await $fetch<EnderecoViaCep>(`https://viacep.com.br/ws/${cep}/json/`)
    if (consulta !== consultaCepAtual) return
    if (endereco.erro) {
      cepErro.value = 'CEP não encontrado.'
      return
    }
    paciente.logradouro = endereco.logradouro ?? ''
    paciente.complemento = endereco.complemento ?? ''
    paciente.bairro = endereco.bairro ?? ''
    paciente.cidade = endereco.localidade ?? ''
    paciente.estadoUf = endereco.uf ?? ''
    paciente.codigoIbge = endereco.ibge ?? ''
  } catch {
    if (consulta === consultaCepAtual) cepErro.value = 'Não foi possível consultar o CEP. Tente novamente.'
  } finally {
    if (consulta === consultaCepAtual) cepBuscando.value = false
  }
}

function encerrarCamera() {
  streamCamera?.getTracks().forEach(track => track.stop())
  streamCamera = null
  if (videoCamera.value) videoCamera.value.srcObject = null
}

async function abrirCamera() {
  cameraErro.value = ''
  cameraAberta.value = true
  if (!navigator.mediaDevices?.getUserMedia) {
    cameraErro.value = 'A câmera não está disponível neste navegador.'
    return
  }
  cameraCarregando.value = true
  try {
    streamCamera = await navigator.mediaDevices.getUserMedia({ video: { facingMode: 'user' }, audio: false })
    await nextTick()
    if (videoCamera.value) {
      videoCamera.value.srcObject = streamCamera
      await videoCamera.value.play()
    }
  } catch {
    cameraErro.value = 'Não foi possível acessar a câmera. Verifique a permissão do navegador.'
    encerrarCamera()
  } finally {
    cameraCarregando.value = false
  }
}

function fecharCamera() {
  cameraAberta.value = false
  encerrarCamera()
}

function capturarFoto() {
  const video = videoCamera.value
  if (!video?.videoWidth || !video.videoHeight) return
  const tamanho = Math.min(video.videoWidth, video.videoHeight)
  const canvas = document.createElement('canvas')
  canvas.width = tamanho
  canvas.height = tamanho
  canvas.getContext('2d')?.drawImage(video, (video.videoWidth - tamanho) / 2, (video.videoHeight - tamanho) / 2, tamanho, tamanho, 0, 0, tamanho, tamanho)
  canvas.toBlob((blob) => {
    if (!blob) return
    fotoPaciente.value = new File([blob], 'foto-paciente.jpg', { type: 'image/jpeg' })
    fecharCamera()
  }, 'image/jpeg', 0.9)
}

watch(() => paciente.cep, (valor) => {
  if (consultaCepTimer) clearTimeout(consultaCepTimer)
  const cep = valor.replace(/\D/g, '')
  const consulta = ++consultaCepAtual
  cepErro.value = ''
  cepBuscando.value = false
  if (cep.length === 8) consultaCepTimer = setTimeout(() => void buscarEnderecoPorCep(cep, consulta), 400)
})
watch(fotoPaciente, (foto) => {
  if (fotoPacienteUrl.value) URL.revokeObjectURL(fotoPacienteUrl.value)
  fotoPacienteUrl.value = foto ? URL.createObjectURL(foto) : null
})
watch(() => paciente.nomeCompleto, (nome) => {
  if (pacienteSelecionado.value && nome !== pacienteSelecionado.value.nome) iniciarPacienteNovo()
})
watch(cameraAberta, (aberta) => {
  if (!aberta) encerrarCamera()
})
onBeforeUnmount(() => {
  encerrarCamera()
  if (consultaCepTimer) clearTimeout(consultaCepTimer)
  if (fotoPacienteUrl.value) URL.revokeObjectURL(fotoPacienteUrl.value)
})
</script>

<template>
  <div>
    <UHeader title="Novo atendimento">
      <template #right>
        <div class="flex items-center gap-2">
          <UBadge
            :label="userName"
            color="neutral"
            variant="soft"
          /><UColorModeButton />
        </div>
      </template>
    </UHeader>
    <div class="min-h-[calc(100vh-var(--ui-header-height))] bg-muted p-4 sm:p-6">
      <UTabs
        v-model="tabAtiva"
        :items="tabItems"
        color="primary"
        size="lg"
        variant="pill"
        :unmount-on-hide="false"
        :ui="{ list: 'bg-default/75 backdrop-blur border border-default', trigger: 'grow', content: 'pt-4' }"
      >
        <template #paciente>
          <UForm
            :state="paciente"
            class="space-y-4"
            @submit="proximoPaciente"
          >
            <CardCadastro
              titulo="Informações pessoais"
              cor="primary"
              icone="i-lucide-user"
              accordion
              aberto-inicialmente
            >
              <div class="grid gap-6 lg:grid-cols-[16.25rem_minmax(0,1fr)]">
                <UFileUpload
                  v-model="fotoPaciente"
                  icon="i-lucide-image"
                  label="Adicionar imagem do paciente"
                  layout="grid"
                  :interactive="false"
                  class="size-65"
                >
                  <template #actions="{ open }">
                    <UButton
                      label="Selecionar imagem"
                      icon="i-lucide-upload"
                      color="neutral"
                      variant="outline"
                      @click="open()"
                    /><UButton
                      label="Abrir câmera"
                      icon="i-lucide-camera"
                      color="neutral"
                      variant="outline"
                      @click="abrirCamera"
                    />
                  </template>
                </UFileUpload>
                <div class="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
                  <UFormField
                    label="Nome completo"
                    name="nomeCompleto"
                    required
                    class="sm:col-span-2 xl:col-span-3"
                  >
                    <UInputMenu
                      v-model="paciente.nomeCompleto"
                      mode="autocomplete"
                      :items="sugestoesPacientes"
                      value-key="label"
                      :filter-fields="['label', 'cpf', 'prontuario']"
                      placeholder="Digite ou pesquise por nome, CPF ou prontuário"
                      icon="i-lucide-search"
                      clear
                      class="w-full"
                    >
                      <template #item-label="{ item }">
                        <div>
                          <p>{{ item.label }}</p><p class="text-xs text-muted">
                            {{ item.cpf }} · {{ item.prontuario }}
                          </p>
                        </div>
                      </template>
                    </UInputMenu>
                  </UFormField>
                  <UFormField
                    label="CPF"
                    name="cpf"
                  >
                    <UInput
                      :model-value="paciente.cpf"
                      placeholder="000.000.000-00"
                      inputmode="numeric"
                      class="w-full"
                      @update:model-value="paciente.cpf = formatarCpf($event)"
                    />
                  </UFormField>
                  <UFormField
                    label="Data de nascimento"
                    name="dataNascimento"
                  >
                    <UInputDate
                      v-model="dataNascimento"
                      class="w-full"
                    />
                  </UFormField>
                  <UFormField
                    label="Nome social"
                    name="nomeSocial"
                    class="xl:col-span-2"
                  >
                    <UInput
                      v-model="paciente.nomeSocial"
                      class="w-full"
                    />
                  </UFormField>
                  <UFormField
                    label="Nome da mãe"
                    name="nomeMae"
                  >
                    <UInput
                      v-model="paciente.nomeMae"
                      class="w-full"
                    />
                  </UFormField>
                  <UFormField
                    label="RG"
                    name="rg"
                  >
                    <UInput
                      v-model="paciente.rg"
                      class="w-full"
                    />
                  </UFormField><UFormField
                    label="Órgão emissor"
                    name="orgaoEmissor"
                  >
                    <UInput
                      v-model="paciente.orgaoEmissor"
                      placeholder="Ex.: SSP"
                      class="w-full"
                    />
                  </UFormField>
                  <UFormField
                    label="Sexo biológico"
                    name="sexoBiologico"
                  >
                    <USelect
                      v-model="paciente.sexoBiologico"
                      :items="opcoesSexo"
                      placeholder="Selecione"
                      class="w-full"
                    />
                  </UFormField><UFormField
                    label="Identidade de gênero"
                    name="identidadeGenero"
                  >
                    <USelect
                      v-model="paciente.identidadeGenero"
                      :items="opcoesGenero"
                      placeholder="Selecione"
                      class="w-full"
                    />
                  </UFormField><UFormField
                    label="Estado civil"
                    name="estadoCivil"
                  >
                    <USelect
                      v-model="paciente.estadoCivil"
                      :items="opcoesEstadoCivil"
                      placeholder="Selecione"
                      class="w-full"
                    />
                  </UFormField>
                  <UFormField
                    label="Nacionalidade"
                    name="nacionalidade"
                  >
                    <UInput
                      v-model="paciente.nacionalidade"
                      class="w-full"
                    />
                  </UFormField><UFormField
                    label="Naturalidade"
                    name="naturalidade"
                    class="xl:col-span-2"
                  >
                    <UInput
                      v-model="paciente.naturalidade"
                      placeholder="Cidade/UF de nascimento"
                      class="w-full"
                    />
                  </UFormField>
                </div>
              </div>
            </CardCadastro>
            <CardCadastro
              titulo="Informações de contato"
              cor="tertiary"
              icone="i-lucide-phone"
            >
              <div class="grid grid-cols-1 gap-4 sm:grid-cols-3">
                <UFormField
                  label="Celular (WhatsApp)"
                  name="celularWhatsapp"
                >
                  <UInput
                    :model-value="paciente.celularWhatsapp"
                    inputmode="tel"
                    class="w-full"
                    @update:model-value="paciente.celularWhatsapp = formatarTelefone($event)"
                  />
                </UFormField><UFormField
                  label="Telefone fixo"
                  name="telefoneFixo"
                >
                  <UInput
                    :model-value="paciente.telefoneFixo"
                    inputmode="tel"
                    class="w-full"
                    @update:model-value="paciente.telefoneFixo = formatarTelefone($event)"
                  />
                </UFormField><UFormField
                  label="E-mail"
                  name="email"
                >
                  <UInput
                    v-model="paciente.email"
                    type="email"
                    class="w-full"
                  />
                </UFormField>
              </div>
            </CardCadastro>
            <CardCadastro
              titulo="Endereço"
              cor="quinary"
              icone="i-lucide-map-pin"
            >
              <div class="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
                <UFormField
                  label="CEP"
                  name="cep"
                  :description="cepErro || undefined"
                >
                  <UInput
                    :model-value="paciente.cep"
                    placeholder="00000-000"
                    inputmode="numeric"
                    :loading="cepBuscando"
                    class="w-full"
                    @update:model-value="paciente.cep = formatarCep($event)"
                  />
                </UFormField><UFormField
                  label="Endereço (logradouro)"
                  name="logradouro"
                  class="sm:col-span-2 xl:col-span-3"
                >
                  <UInput
                    v-model="paciente.logradouro"
                    class="w-full"
                  />
                </UFormField><UFormField
                  label="Número"
                  name="numero"
                >
                  <UInput
                    v-model="paciente.numero"
                    class="w-full"
                  />
                </UFormField><UFormField
                  label="Complemento"
                  name="complemento"
                >
                  <UInput
                    v-model="paciente.complemento"
                    class="w-full"
                  />
                </UFormField><UFormField
                  label="Bairro"
                  name="bairro"
                  class="sm:col-span-2"
                >
                  <UInput
                    v-model="paciente.bairro"
                    class="w-full"
                  />
                </UFormField><UFormField
                  label="Cidade"
                  name="cidade"
                  class="sm:col-span-2"
                >
                  <UInput
                    v-model="paciente.cidade"
                    class="w-full"
                  />
                </UFormField><UFormField
                  label="UF"
                  name="estadoUf"
                >
                  <USelect
                    v-model="paciente.estadoUf"
                    :items="estadosBr"
                    placeholder="Selecione"
                    class="w-full"
                  />
                </UFormField><UFormField
                  label="Código IBGE"
                  name="codigoIbge"
                >
                  <UInput
                    v-model="paciente.codigoIbge"
                    inputmode="numeric"
                    class="w-full"
                  />
                </UFormField>
              </div>
            </CardCadastro>
            <div class="flex justify-end">
              <UButton
                type="submit"
                label="Próximo"
                trailing-icon="i-lucide-arrow-right"
                size="lg"
                class="w-full sm:w-auto"
              />
            </div>
          </UForm>
        </template>
        <template #atendimento>
          <UForm
            :state="atendimento"
            class="space-y-4"
            @submit="proximoAtendimento"
          >
            <UCard>
              <div class="flex flex-col gap-4 sm:flex-row sm:items-center">
                <UAvatar
                  :src="fotoPacienteUrl || undefined"
                  :alt="paciente.nomeCompleto"
                  color="primary"
                  size="xl"
                />
                <div class="min-w-0 flex-1">
                  <p class="truncate text-lg font-semibold text-highlighted">
                    {{ paciente.nomeCompleto }}
                  </p>
                  <p class="text-sm text-muted">
                    Prontuário {{ prontuarioAtual }}
                  </p>
                  <div class="mt-3 grid grid-cols-2 gap-x-4 gap-y-2 text-sm sm:grid-cols-4">
                    <p><span class="text-muted">CPF:</span> {{ paciente.cpf || '-' }}</p>
                    <p><span class="text-muted">Sexo:</span> {{ paciente.sexoBiologico || '-' }}</p>
                    <p><span class="text-muted">Idade:</span> {{ idadePaciente || '-' }}</p>
                    <p><span class="text-muted">Cidade:</span> {{ paciente.cidade ? `${paciente.cidade}/${paciente.estadoUf}` : '-' }}</p>
                  </div>
                </div>
              </div>
            </UCard>
            <CardCadastro
              titulo="Dados do atendimento"
              cor="secondary"
              icone="i-lucide-stethoscope"
            >
              <div class="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
                <UFormField
                  label="Nº do registro"
                  name="registro"
                >
                  <UInput
                    v-model="atendimento.registro"
                    class="w-full"
                  />
                </UFormField><UFormField
                  label="Data de entrada"
                  name="dataEntrada"
                >
                  <UInputDate
                    v-model="dataEntrada"
                    class="w-full"
                  />
                </UFormField><UFormField
                  label="Hora"
                  name="horaEntrada"
                >
                  <UInputTime
                    v-model="horaEntrada"
                    class="w-full"
                  />
                </UFormField><UFormField
                  label="Caráter da solicitação"
                  name="caraterSolicitacao"
                >
                  <USelect
                    v-model="atendimento.caraterSolicitacao"
                    :items="opcoesCarater"
                    placeholder="Selecione"
                    class="w-full"
                  />
                </UFormField><UFormField
                  label="Cód. procedimento"
                  name="codigoProcedimento"
                >
                  <UInput
                    v-model="atendimento.codigoProcedimento"
                    class="w-full"
                  />
                </UFormField><UFormField
                  label="Nome do procedimento"
                  name="nomeProcedimento"
                  class="sm:col-span-2"
                >
                  <UInput
                    v-model="atendimento.nomeProcedimento"
                    class="w-full"
                  />
                </UFormField><UFormField
                  label="Tipo"
                  name="tipoProcedimento"
                >
                  <USelect
                    v-model="atendimento.tipoProcedimento"
                    :items="opcoesTipo"
                    placeholder="Selecione"
                    class="w-full"
                  />
                </UFormField><UFormField
                  label="Modalidade"
                  name="modalidade"
                >
                  <USelect
                    v-model="atendimento.modalidade"
                    :items="opcoesModalidade"
                    placeholder="Selecione"
                    class="w-full"
                  />
                </UFormField><UFormField
                  name="ehRetorno"
                  class="flex items-end"
                >
                  <USwitch
                    v-model="atendimento.ehRetorno"
                    label="É retorno?"
                  />
                </UFormField><UFormField
                  name="recemNascido"
                  class="flex items-end"
                >
                  <USwitch
                    v-model="atendimento.recemNascido"
                    label="Recém-nascido?"
                  />
                </UFormField><UFormField
                  name="atualizaFaturamento"
                  class="flex items-end"
                >
                  <USwitch
                    v-model="atendimento.atualizaFaturamento"
                    label="Atualiza faturamento"
                  />
                </UFormField>
              </div>
            </CardCadastro>
            <CardCadastro
              titulo="Convênio e plano"
              cor="tertiary"
              icone="i-lucide-credit-card"
            >
              <div class="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
                <UFormField
                  label="Convênio (número)"
                  name="numeroConvenio"
                >
                  <UInput
                    v-model="atendimento.numeroConvenio"
                    class="w-full"
                  />
                </UFormField><UFormField
                  label="Descrição"
                  name="descricaoConvenio"
                  class="sm:col-span-2"
                >
                  <UInput
                    v-model="atendimento.descricaoConvenio"
                    readonly
                    placeholder="Preenchida pelo número do convênio"
                    class="w-full"
                  />
                </UFormField><UFormField
                  label="Matrícula"
                  name="matricula"
                >
                  <UInput
                    v-model="atendimento.matricula"
                    class="w-full"
                  />
                </UFormField><UFormField
                  label="Validade"
                  name="validade"
                >
                  <UInput
                    v-model="atendimento.validade"
                    placeholder="MM/AAAA"
                    class="w-full"
                  />
                </UFormField><UFormField
                  label="Guia de autorização"
                  name="guiaAutorizacao"
                  class="sm:col-span-2 xl:col-span-3"
                >
                  <UInput
                    v-model="atendimento.guiaAutorizacao"
                    class="w-full"
                  />
                </UFormField>
              </div>
            </CardCadastro>
            <CardCadastro
              titulo="Médico & unidade"
              cor="quinary"
              icone="i-lucide-building-2"
            >
              <div class="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-5">
                <UFormField
                  label="CRM"
                  name="crm"
                >
                  <UInput
                    v-model="atendimento.crm"
                    class="w-full"
                  />
                </UFormField><UFormField
                  label="Nome do médico"
                  name="nomeMedico"
                  class="sm:col-span-2"
                >
                  <UInput
                    v-model="atendimento.nomeMedico"
                    class="w-full"
                  />
                </UFormField><UFormField
                  label="Especialidade"
                  name="especialidade"
                >
                  <UInput
                    v-model="atendimento.especialidade"
                    class="w-full"
                  />
                </UFormField><UFormField
                  label="C.D.C. número"
                  name="centroCustoNumero"
                >
                  <UInput
                    v-model="atendimento.centroCustoNumero"
                    class="w-full"
                  />
                </UFormField><UFormField
                  label="C.D.C. nome"
                  name="centroCustoNome"
                >
                  <UInput
                    v-model="atendimento.centroCustoNome"
                    class="w-full"
                  />
                </UFormField><UFormField
                  label="Unidade"
                  name="unidade"
                  class="sm:col-span-2"
                >
                  <UInput
                    v-model="atendimento.unidade"
                    class="w-full"
                  />
                </UFormField>
              </div>
            </CardCadastro>
            <div class="flex flex-col-reverse gap-2 sm:flex-row sm:justify-between">
              <UButton
                label="Voltar"
                color="neutral"
                variant="outline"
                icon="i-lucide-arrow-left"
                @click="void (tabAtiva = 'paciente')"
              /><UButton
                type="submit"
                label="Próximo"
                trailing-icon="i-lucide-arrow-right"
              />
            </div>
          </UForm>
        </template>
        <template #responsavel>
          <UForm
            :state="responsavel"
            class="space-y-4"
            @submit="finalizarCadastro"
          >
            <CardCadastro
              titulo="Responsável pelo paciente"
              cor="quaternary"
              icone="i-lucide-users"
              accordion
              aberto-inicialmente
            >
              <div class="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
                <UFormField
                  label="Nome do responsável"
                  name="nome"
                  class="sm:col-span-2"
                >
                  <UInput
                    v-model="responsavel.nome"
                    class="w-full"
                  />
                </UFormField><UFormField
                  label="Identidade"
                  name="identidade"
                >
                  <UInput
                    v-model="responsavel.identidade"
                    class="w-full"
                  />
                </UFormField><UFormField
                  label="CPF"
                  name="cpf"
                >
                  <UInput
                    :model-value="responsavel.cpf"
                    inputmode="numeric"
                    class="w-full"
                    @update:model-value="responsavel.cpf = formatarCpf($event)"
                  />
                </UFormField><UFormField
                  label="CNPJ"
                  name="cnpj"
                >
                  <UInput
                    :model-value="responsavel.cnpj"
                    inputmode="numeric"
                    class="w-full"
                    @update:model-value="responsavel.cnpj = formatarCpfCnpj($event)"
                  />
                </UFormField><UFormField
                  label="Data de nascimento"
                  name="dataNascimento"
                >
                  <UInputDate
                    v-model="dataNascimentoResponsavel"
                    class="w-full"
                  />
                </UFormField><UFormField
                  label="Parentesco"
                  name="parentesco"
                >
                  <UInput
                    v-model="responsavel.parentesco"
                    class="w-full"
                  />
                </UFormField><UFormField
                  label="Profissão"
                  name="profissao"
                >
                  <UInput
                    v-model="responsavel.profissao"
                    class="w-full"
                  />
                </UFormField><UFormField
                  label="CEP"
                  name="cep"
                >
                  <UInput
                    :model-value="responsavel.cep"
                    inputmode="numeric"
                    class="w-full"
                    @update:model-value="responsavel.cep = formatarCep($event)"
                  />
                </UFormField><UFormField
                  label="Endereço"
                  name="logradouro"
                  class="sm:col-span-2 xl:col-span-3"
                >
                  <UInput
                    v-model="responsavel.logradouro"
                    class="w-full"
                  />
                </UFormField><UFormField
                  label="Número"
                  name="numero"
                >
                  <UInput
                    v-model="responsavel.numero"
                    class="w-full"
                  />
                </UFormField><UFormField
                  label="Complemento"
                  name="complemento"
                >
                  <UInput
                    v-model="responsavel.complemento"
                    class="w-full"
                  />
                </UFormField><UFormField
                  label="Bairro"
                  name="bairro"
                  class="sm:col-span-2"
                >
                  <UInput
                    v-model="responsavel.bairro"
                    class="w-full"
                  />
                </UFormField><UFormField
                  label="Cidade"
                  name="cidade"
                  class="sm:col-span-2"
                >
                  <UInput
                    v-model="responsavel.cidade"
                    class="w-full"
                  />
                </UFormField><UFormField
                  label="UF"
                  name="uf"
                >
                  <USelect
                    v-model="responsavel.uf"
                    :items="estadosBr"
                    placeholder="Selecione"
                    class="w-full"
                  />
                </UFormField><UFormField
                  label="Telefone"
                  name="telefone"
                >
                  <UInput
                    :model-value="responsavel.telefone"
                    inputmode="tel"
                    class="w-full"
                    @update:model-value="responsavel.telefone = formatarTelefone($event)"
                  />
                </UFormField>
              </div>
            </CardCadastro>
            <div class="flex flex-col-reverse gap-2 sm:flex-row sm:justify-between">
              <UButton
                label="Voltar"
                color="neutral"
                variant="outline"
                icon="i-lucide-arrow-left"
                @click="void (tabAtiva = 'atendimento')"
              /><UButton
                type="submit"
                label="Finalizar cadastro"
                icon="i-lucide-circle-check"
              />
            </div>
          </UForm>
        </template>
      </UTabs>
    </div>
    <UModal
      v-model:open="cameraAberta"
      title="Capturar foto do paciente"
      description="Posicione o rosto do paciente na área da câmera."
    >
      <template #body>
        <div class="space-y-4">
          <div class="aspect-square overflow-hidden rounded-lg bg-elevated">
            <video
              v-if="!cameraErro"
              ref="videoCamera"
              autoplay
              muted
              playsinline
              class="size-full object-cover"
            /><div
              v-else
              class="flex size-full items-center justify-center p-6 text-center text-sm text-error"
            >
              {{ cameraErro }}
            </div>
          </div><p
            v-if="cameraCarregando"
            class="text-sm text-muted"
          >
            Iniciando câmera...
          </p>
        </div>
      </template><template #footer>
        <UButton
          label="Cancelar"
          color="neutral"
          variant="outline"
          @click="fecharCamera"
        /><UButton
          label="Capturar foto"
          icon="i-lucide-camera"
          :disabled="cameraCarregando || Boolean(cameraErro)"
          @click="capturarFoto"
        />
      </template>
    </UModal>
  </div>
</template>
