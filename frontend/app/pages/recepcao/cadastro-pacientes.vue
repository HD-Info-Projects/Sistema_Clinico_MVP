<script setup lang="ts">
import type { CalendarDate } from '@internationalized/date'
import { formatarCpf, formatarTelefone } from '~/utils/masks'

interface EnderecoViaCep {
  erro?: boolean
  logradouro?: string
  complemento?: string
  bairro?: string
  localidade?: string
  uf?: string
  ibge?: string
}

const auth = useAuthStore()
const toast = useToast()

const userName = computed(() => auth.user?.nome || 'Usuário')
const fotoPaciente = ref<File | null>(null)
const dataNascimento = shallowRef<CalendarDate | null>(null)
const salvando = ref(false)
const dadosPessoais = reactive({
  nomeCompleto: '',
  nomeSocial: '',
  chamarNomeSocial: false,
  cpf: '',
  nomeMae: '',
  maeDesconhecida: false,
  rg: '',
  orgaoEmissor: '',
  sexoBiologico: '',
  identidadeGenero: '',
  estadoCivil: '',
  nacionalidade: '',
  naturalidade: '',
  celularWhatsapp: '',
  telefoneFixo: '',
  email: '',
  cep: '',
  logradouro: '',
  numero: '',
  complemento: '',
  bairro: '',
  cidade: '',
  estadoUf: '',
  codigoIbge: ''
})
const opcoesSexoBiologico = [
  { label: 'Masculino', value: 'masculino' },
  { label: 'Feminino', value: 'feminino' },
  { label: 'Intersexo', value: 'intersexo' },
  { label: 'Prefiro não informar', value: 'nao_informar' }
]
const opcoesIdentidadeGenero = [
  { label: 'Mulher cisgênero', value: 'mulher_cisgenero' },
  { label: 'Homem cisgênero', value: 'homem_cisgenero' },
  { label: 'Mulher transgênero', value: 'mulher_transgenero' },
  { label: 'Homem transgênero', value: 'homem_transgenero' },
  { label: 'Não binário', value: 'nao_binario' },
  { label: 'Outra', value: 'outra' },
  { label: 'Prefiro não informar', value: 'nao_informar' }
]
const opcoesEstadoCivil = [
  { label: 'Solteiro(a)', value: 'solteiro' },
  { label: 'Casado(a)', value: 'casado' },
  { label: 'União estável', value: 'uniao_estavel' },
  { label: 'Divorciado(a)', value: 'divorciado' },
  { label: 'Viúvo(a)', value: 'viuvo' },
  { label: 'Prefiro não informar', value: 'nao_informar' }
]
const estadosBr = [
  'AC', 'AL', 'AP', 'AM', 'BA', 'CE', 'DF', 'ES', 'GO', 'MA',
  'MT', 'MS', 'MG', 'PA', 'PB', 'PR', 'PE', 'PI', 'RJ', 'RN',
  'RS', 'RO', 'RR', 'SC', 'SP', 'SE', 'TO'
]
const cepBuscando = ref(false)
const cepErro = ref('')
const cameraAberta = ref(false)
const cameraCarregando = ref(false)
const cameraErro = ref('')
const videoCamera = ref<HTMLVideoElement | null>(null)
let streamCamera: MediaStream | null = null
let consultaCepTimer: ReturnType<typeof setTimeout> | null = null
let consultaCepAtual = 0

function mensagemErro(error: unknown, fallback: string) {
  const err = error as { data?: { error?: string, message?: string }, message?: string }
  return err.data?.error || err.data?.message || err.message || fallback
}

function dataCalendarIso(data: CalendarDate | null) {
  if (!data) return null
  return `${data.year}-${String(data.month).padStart(2, '0')}-${String(data.day).padStart(2, '0')}`
}

function payloadPaciente() {
  return {
    ...dadosPessoais,
    dataNascimento: dataCalendarIso(dataNascimento.value)
  }
}

async function finalizarCadastro() {
  if (!dadosPessoais.nomeCompleto.trim()) {
    toast.add({ title: 'Informe o nome completo do paciente.', color: 'error' })
    return
  }

  salvando.value = true
  try {
    const resultado = await $fetch<{ paciente?: { idPacienteSpdata?: number, prontuario?: string }, created?: boolean }>('/api/recepcao/pacientes', {
      method: 'POST',
      body: payloadPaciente()
    })
    const paciente = resultado.paciente
    toast.add({
      title: resultado.created ? 'Paciente cadastrado no SPDATA.' : 'Paciente atualizado no SPDATA.',
      description: paciente?.prontuario ? `Prontuário ${paciente.prontuario}` : undefined,
      color: 'success'
    })

    if (paciente?.idPacienteSpdata) {
      await navigateTo(`/recepcao/cadastro-atendimento?pacienteId=${paciente.idPacienteSpdata}`)
    }
  } catch (error) {
    toast.add({ title: mensagemErro(error, 'Não foi possível salvar o paciente.'), color: 'error' })
  } finally {
    salvando.value = false
  }
}

function encerrarCamera() {
  streamCamera?.getTracks().forEach(track => track.stop())
  streamCamera = null

  if (videoCamera.value) videoCamera.value.srcObject = null
}

async function abrirCamera() {
  cameraErro.value = ''

  if (!navigator.mediaDevices?.getUserMedia) {
    cameraErro.value = 'A câmera não está disponível neste navegador.'
    cameraAberta.value = true
    return
  }

  cameraCarregando.value = true
  cameraAberta.value = true

  try {
    streamCamera = await navigator.mediaDevices.getUserMedia({
      video: { facingMode: 'user' },
      audio: false
    })

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
  if (!video || !video.videoWidth || !video.videoHeight) return

  const canvas = document.createElement('canvas')
  const tamanho = Math.min(video.videoWidth, video.videoHeight)
  const origemX = (video.videoWidth - tamanho) / 2
  const origemY = (video.videoHeight - tamanho) / 2
  canvas.width = tamanho
  canvas.height = tamanho
  canvas.getContext('2d')?.drawImage(video, origemX, origemY, tamanho, tamanho, 0, 0, tamanho, tamanho)

  canvas.toBlob((blob) => {
    if (!blob) {
      toast.add({ title: 'Não foi possível capturar a foto.', color: 'error' })
      return
    }

    fotoPaciente.value = new File([blob], 'foto-paciente.jpg', { type: 'image/jpeg' })
    fecharCamera()
  }, 'image/jpeg', 0.9)
}

function formatarCep(valor: string) {
  const digitos = valor.replace(/\D/g, '').slice(0, 8)
  return digitos.length > 5 ? `${digitos.slice(0, 5)}-${digitos.slice(5)}` : digitos
}

function formatarCodigoIbge(valor: string) {
  return valor.replace(/\D/g, '').slice(0, 7)
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

    if (!dadosPessoais.logradouro && endereco.logradouro) dadosPessoais.logradouro = endereco.logradouro
    if (!dadosPessoais.complemento && endereco.complemento) dadosPessoais.complemento = endereco.complemento
    if (!dadosPessoais.bairro && endereco.bairro) dadosPessoais.bairro = endereco.bairro
    if (!dadosPessoais.cidade && endereco.localidade) dadosPessoais.cidade = endereco.localidade
    if (!dadosPessoais.estadoUf && endereco.uf) dadosPessoais.estadoUf = endereco.uf
    if (!dadosPessoais.codigoIbge && endereco.ibge) dadosPessoais.codigoIbge = endereco.ibge
  } catch {
    if (consulta === consultaCepAtual) {
      cepErro.value = 'Não foi possível consultar o CEP. Tente novamente.'
    }
  } finally {
    if (consulta === consultaCepAtual) cepBuscando.value = false
  }
}

watch(() => dadosPessoais.cep, (cepFormatado) => {
  if (consultaCepTimer) clearTimeout(consultaCepTimer)

  const cep = cepFormatado.replace(/\D/g, '')
  const consulta = ++consultaCepAtual
  cepErro.value = ''
  cepBuscando.value = false

  if (cep.length !== 8) return

  consultaCepTimer = setTimeout(() => {
    void buscarEnderecoPorCep(cep, consulta)
  }, 400)
})

watch(cameraAberta, (aberta) => {
  if (!aberta) encerrarCamera()
})

onBeforeUnmount(() => {
  encerrarCamera()
  if (consultaCepTimer) clearTimeout(consultaCepTimer)
})
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

    <div class="min-h-[calc(100vh-var(--ui-header-height))] bg-muted p-4 sm:p-6 sm:py-2">
      <div class="p-2 flex items-center gap-2 ">
        <UIcon name="i-lucide-info" />
        <p class="text-base text-muted ">
          Preencha os campos abaixo para cadastrar um novo paciente no sistema.
        </p>
      </div>
      <UForm
        :state="dadosPessoais"
        class="flex flex-col gap-4 "
      >
        <!--  Informações Pessoais  -->
        <CardCadastro
          titulo="Informações Pessoais"
          cor="primary"
          icone="i-lucide-user"
        >
          <div class="grid gap-6 lg:grid-cols-[16.25rem_minmax(0,1fr)] lg:items-start">
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
                />
                <UButton
                  label="Abrir câmera"
                  icon="i-lucide-camera"
                  color="neutral"
                  variant="outline"
                  @click="abrirCamera"
                />
              </template>
            </UFileUpload>

            <div class="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4 xl:grid-cols-6">
              <UFormField
                label="Nome completo"
                name="nomeCompleto"
                class="sm:col-span-2 lg:col-span-2 xl:col-span-4"
              >
                <UInput
                  v-model="dadosPessoais.nomeCompleto"
                  placeholder="Nome completo do paciente"
                  class="w-full"
                />
              </UFormField>
              <UFormField
                label="CPF"
                name="cpf"
              >
                <UInput
                  :model-value="dadosPessoais.cpf"
                  placeholder="000.000.000-00"
                  inputmode="numeric"
                  class="w-full"
                  @update:model-value="dadosPessoais.cpf = formatarCpf($event)"
                />
              </UFormField>

              <UFormField
                label="Data de Nascimento"
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
                class="lg:col-span-2 xl:col-span-3"
              >
                <UInput
                  v-model="dadosPessoais.nomeSocial"
                  placeholder="Como o paciente prefere ser chamado"
                  class="w-full"
                />
              </UFormField>

              <UCheckbox
                v-model="dadosPessoais.chamarNomeSocial"
                label="Chamar pelo nome social"
                class="lg:col-span-1 xl:col-span-1 pt-7"
              />

              <UFormField
                label="RG"
                name="rg"
              >
                <UInput
                  v-model="dadosPessoais.rg"
                  placeholder="Número do RG"
                  class="w-full"
                />
              </UFormField>

              <UFormField
                label="Órgão emissor"
                name="orgaoEmissor"
              >
                <UInput
                  v-model="dadosPessoais.orgaoEmissor"
                  placeholder="Ex.: SSP"
                  class="w-full"
                />
              </UFormField>

              <UFormField
                label="Sexo biológico"
                name="sexoBiologico"
              >
                <USelect
                  v-model="dadosPessoais.sexoBiologico"
                  :items="opcoesSexoBiologico"
                  placeholder="Selecione"
                  class="w-full"
                />
              </UFormField>

              <UFormField
                label="Identidade de gênero"
                name="identidadeGenero"
              >
                <USelect
                  v-model="dadosPessoais.identidadeGenero"
                  :items="opcoesIdentidadeGenero"
                  placeholder="Selecione"
                  class="w-full"
                />
              </UFormField>

              <UFormField
                label="Estado civil"
                name="estadoCivil"
              >
                <USelect
                  v-model="dadosPessoais.estadoCivil"
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
                  v-model="dadosPessoais.nacionalidade"
                  placeholder="Ex.: Brasileira"
                  class="w-full"
                />
              </UFormField>

              <UFormField
                label="Naturalidade"
                name="naturalidade"
                class="sm:col-span-1 lg:col-span-2 xl:col-span-2"
              >
                <UInput
                  v-model="dadosPessoais.naturalidade"
                  placeholder="Cidade/UF de nascimento"
                  class="w-full"
                />
              </UFormField>

              <UCheckbox
                v-model="dadosPessoais.maeDesconhecida"
                label="Mãe desconhecida"
                class="lg:col-span-1 xl:col-span-1"
              />

              <UFormField
                v-if="!dadosPessoais.maeDesconhecida"
                label="Nome da mãe"
                name="nomeMae"
                class="sm:col-span-2 xl:col-span-3"
              >
                <UInput

                  v-model="dadosPessoais.nomeMae"
                  placeholder="Nome completo da mãe"
                  class="w-full"
                />
              </UFormField>
            </div>
          </div>
        </CardCadastro>
        <!--  Informações de Contato  -->
        <CardCadastro
          titulo="Informações de Contato"
          cor="tertiary"
          icone="i-lucide-phone"
        >
          <div class="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-3">
            <UFormField
              label="Celular (WhatsApp)"
              name="celularWhatsapp"
            >
              <UInput
                :model-value="dadosPessoais.celularWhatsapp"
                placeholder="(00) 00000-0000"
                inputmode="tel"
                class="w-full"
                @update:model-value="dadosPessoais.celularWhatsapp = formatarTelefone($event)"
              />
            </UFormField>

            <UFormField
              label="Telefone fixo"
              name="telefoneFixo"
            >
              <UInput
                :model-value="dadosPessoais.telefoneFixo"
                placeholder="(00) 0000-0000"
                inputmode="tel"
                class="w-full"
                @update:model-value="dadosPessoais.telefoneFixo = formatarTelefone($event)"
              />
            </UFormField>

            <UFormField
              label="E-mail"
              name="email"
            >
              <UInput
                v-model="dadosPessoais.email"
                type="email"
                placeholder="nome@exemplo.com"
                class="w-full"
              />
            </UFormField>
          </div>
        </CardCadastro>
        <!--  Endereço  -->
        <CardCadastro
          titulo="Endereço"
          cor="quinary"
          icone="i-lucide-map-pin"
        >
          <div class="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-6">
            <UFormField
              label="CEP"
              name="cep"
              :description="cepErro || undefined"
            >
              <UInput
                :model-value="dadosPessoais.cep"
                placeholder="00000-000"
                inputmode="numeric"
                :loading="cepBuscando"
                class="w-full"
                @update:model-value="dadosPessoais.cep = formatarCep($event)"
              />
            </UFormField>

            <UFormField
              label="Endereço (logradouro)"
              name="logradouro"
              class="sm:col-span-2 xl:col-span-3"
            >
              <UInput
                v-model="dadosPessoais.logradouro"
                placeholder="Rua, avenida, travessa..."
                class="w-full"
              />
            </UFormField>

            <UFormField
              label="Bairro"
              name="bairro"
              class="sm:col-span-2 xl:col-span-1"
            >
              <UInput
                v-model="dadosPessoais.bairro"
                placeholder="Bairro"
                class="w-full"
              />
            </UFormField>

            <UFormField
              label="Cidade"
              name="cidade"
              class="sm:col-span-2 xl:col-span-1"
            >
              <UInput
                v-model="dadosPessoais.cidade"
                placeholder="Cidade"
                class="w-full"
              />
            </UFormField>

            <UFormField
              label="Número"
              name="numero"
            >
              <UInput
                v-model="dadosPessoais.numero"
                placeholder="Número"
                class="w-full"
              />
            </UFormField>

            <UFormField
              label="Complemento"
              name="complemento"
              class="sm:col-span-2 xl:col-span-3"
            >
              <UInput
                v-model="dadosPessoais.complemento"
                placeholder="Apto., bloco..."
                class="w-full"
              />
            </UFormField>

            <UFormField
              label="Estado (UF)"
              name="estadoUf"
            >
              <USelect
                v-model="dadosPessoais.estadoUf"
                :items="estadosBr"
                placeholder="Selecione"
                class="w-full"
              />
            </UFormField>

            <UFormField
              label="Código IBGE"
              name="codigoIbge"
            >
              <UInput
                :model-value="dadosPessoais.codigoIbge"
                placeholder="0000000"
                inputmode="numeric"
                class="w-full"
                @update:model-value="dadosPessoais.codigoIbge = formatarCodigoIbge($event)"
              />
            </UFormField>
          </div>
        </CardCadastro>

        <div class="flex pt-2 sm:justify-end">
          <UButton
            type="button"
            label="Finalizar cadastro"
            icon="i-lucide-circle-check"
            size="lg"
            :loading="salvando"
            :disabled="salvando"
            class="w-full sm:w-auto"
            @click="finalizarCadastro"
          />
        </div>
      </UForm>
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
            />
            <div
              v-else
              class="flex size-full items-center justify-center p-6 text-center text-sm text-error"
            >
              {{ cameraErro }}
            </div>
          </div>
          <p
            v-if="cameraCarregando"
            class="text-sm text-muted"
          >
            Iniciando câmera...
          </p>
        </div>
      </template>

      <template #footer>
        <UButton
          label="Cancelar"
          color="neutral"
          variant="outline"
          @click="fecharCamera"
        />
        <UButton
          label="Capturar foto"
          icon="i-lucide-camera"
          :disabled="cameraCarregando || Boolean(cameraErro)"
          @click="capturarFoto"
        />
      </template>
    </UModal>
  </div>
</template>
