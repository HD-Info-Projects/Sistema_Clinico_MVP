<script setup lang="ts">
import type { AgendamentoComPaciente, DocumentoPersonalizado } from '~/types'
import { excluirDocumentoPersonalizado } from '~/features/documentos/services/documentosService'
import { usePdfMake } from '~/utils/pdf'
import { buildDocumentoPersonalizado } from '~/utils/pdf-documents'

const props = defineProps<{
  agendamento?: AgendamentoComPaciente | null
  documentos: DocumentoPersonalizado[]
}>()

const emit = defineEmits<{
  saved: [documento: DocumentoPersonalizado]
}>()

const open = defineModel<boolean>('open', { default: false })
const editorOpen = ref(false)
const documentoEmEdicao = ref<DocumentoPersonalizado | null>(null)
const documentosLocais = ref<DocumentoPersonalizado[]>([])
const documentoParaExcluir = ref<DocumentoPersonalizado | null>(null)
const toast = useToast()

const podeCriar = computed(() => documentosLocais.value.every(documento => documento.podeEditar))

watch(
  () => [open.value, props.documentos] as const,
  ([isOpen]) => {
    if (isOpen) documentosLocais.value = [...props.documentos]
  },
  { immediate: true }
)

function criarNovo() {
  documentoEmEdicao.value = null
  open.value = false
  editorOpen.value = true
}

function editar(documento: DocumentoPersonalizado) {
  if (!documento.podeEditar) return
  documentoEmEdicao.value = documento
  open.value = false
  editorOpen.value = true
}

function atualizarDocumento(documento: DocumentoPersonalizado) {
  documentosLocais.value = [
    ...documentosLocais.value.filter(item => item.id !== documento.id),
    documento
  ].sort((a, b) => a.id - b.id)
  emit('saved', documento)
  open.value = true
}

async function imprimirTodos() {
  if (!documentosLocais.value.length) return
  open.value = false
  await nextTick()
  const pdfMake = await usePdfMake()
  const doc = await buildDocumentoPersonalizado({ documentos: documentosLocais.value })
  pdfMake.createPdf(doc).open()
}

async function imprimirDocumento(documento: DocumentoPersonalizado) {
  const pdfMake = await usePdfMake()
  const doc = await buildDocumentoPersonalizado({ documentos: [documento] })
  pdfMake.createPdf(doc).open()
}

async function excluirDocumento() {
  const documento = documentoParaExcluir.value
  if (!documento || !props.agendamento || !documento.podeEditar) return

  try {
    await excluirDocumentoPersonalizado(props.agendamento.id, documento.id)
    documentosLocais.value = documentosLocais.value.filter(item => item.id !== documento.id)
    documentoParaExcluir.value = null
  } catch {
    toast.add({
      title: 'Erro ao excluir documento',
      description: 'Não foi possível excluir o documento personalizado.',
      color: 'error',
      icon: 'i-lucide-alert-circle'
    })
  }
}
</script>

<template>
  <UModal
    v-model:open="open"
    title="Documentos médicos"
    description="Documentos e laudos personalizados desta consulta"
    :ui="{ content: 'max-h-dvh sm:max-h-[calc(100dvh-2rem)]', body: 'min-h-0 overflow-y-auto', footer: 'shrink-0' }"
  >
    <template #body>
      <div class="flex min-h-48 flex-col gap-3">
        <div
          v-if="documentosLocais.length"
          class="flex flex-col gap-2"
        >
          <div
            v-for="documento in documentosLocais"
            :key="documento.id"
            class="flex min-w-0 flex-col gap-2 border-b border-muted p-3 hover:bg-muted/50 sm:flex-row sm:items-center sm:justify-between"
          >
            <button
              type="button"
              class="min-w-0 text-left"
              :class="documento.podeEditar ? 'cursor-pointer' : 'cursor-default'"
              :disabled="!documento.podeEditar"
              @click="editar(documento)"
            >
              <p class="wrap-break-word font-medium">
                {{ documento.titulo }}
              </p>
              <p class="text-xs text-muted">
                Documento médico personalizado
                <span v-if="documento.updatedAt">&middot; {{ new Date(documento.updatedAt).toLocaleDateString('pt-BR') }}</span>
              </p>
            </button>
            <div class="flex shrink-0 self-end gap-1 sm:self-auto">
              <UButton
                icon="i-lucide-printer"
                color="neutral"
                variant="ghost"
                size="sm"
                class="min-h-11 min-w-11 sm:min-h-8 sm:min-w-8"
                :aria-label="`Imprimir ${documento.titulo}`"
                @click="void imprimirDocumento(documento)"
              />
              <UButton
                v-if="documento.podeEditar"
                icon="i-lucide-trash-2"
                color="error"
                variant="ghost"
                size="sm"
                class="min-h-11 min-w-11 sm:min-h-8 sm:min-w-8"
                :aria-label="`Excluir ${documento.titulo}`"
                @click="void(documentoParaExcluir = documento)"
              />
            </div>
          </div>
        </div>
        <div
          v-else
          class="flex min-h-32 flex-col items-center justify-center gap-2 rounded-lg border border-dashed border-muted p-6 text-center"
        >
          <UIcon
            name="i-lucide-file-plus-2"
            class="size-8 text-muted"
          />
          <p class="text-sm text-muted">
            Nenhum documento personalizado foi criado para esta consulta.
          </p>
        </div>
      </div>
    </template>

    <template #footer>
      <div class="flex w-full flex-col-reverse gap-2 sm:flex-row sm:justify-end">
        <UButton
          v-if="documentosLocais.length"
          label="Imprimir todos"
          icon="i-lucide-printer"
          color="neutral"
          variant="soft"
          class="w-full justify-center sm:w-auto"
          @click="void imprimirTodos()"
        />
        <UButton
          v-if="podeCriar"
          label="Criar novo"
          icon="i-lucide-plus"
          color="primary"
          class="w-full justify-center sm:w-auto"
          @click="criarNovo"
        />
      </div>
    </template>
  </UModal>

  <DocumentoPersonalizadoEditorModal
    v-model:open="editorOpen"
    :agendamento="agendamento"
    :documento="documentoEmEdicao"
    @saved="atualizarDocumento"
    @cancelled="open = true"
  />

  <ModalConfirmacao
    :abrir="Boolean(documentoParaExcluir)"
    titulo="Excluir documento?"
    :descricao="`O documento '${documentoParaExcluir?.titulo ?? ''}' será excluído permanentemente.`"
    texto-confirma="Excluir"
    cor-confirma="error"
    :icone="'i-lucide-trash-2'"
    @fechar="documentoParaExcluir = null"
    @confirmar="void excluirDocumento()"
  />
</template>
