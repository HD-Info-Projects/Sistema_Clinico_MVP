<script setup lang="ts">
import type { Unidade, UnidadeForm } from '~/types'

const props = defineProps<{
  unidade?: Unidade | null
}>()

const open = defineModel<boolean>('open', { default: false })
const emit = defineEmits<{ saved: [] }>()

const unidadesStore = useUnidadesStore()
const toast = useToast()

const form = ref<UnidadeForm>({
  nome: '',
  codigo_spdata_centro_custo: '',
  codigo_spdata_agenda: '',
  endereco: '',
  telefone: '',
  ativa: true
})

const saving = ref(false)

const titulo = computed(() => props.unidade ? 'Editar Unidade' : 'Nova Unidade')

watch(open, (isOpen) => {
  if (isOpen) {
    if (props.unidade) {
      form.value = {
        nome: props.unidade.nome,
        codigo_spdata_centro_custo: props.unidade.codigo_spdata_centro_custo,
        codigo_spdata_agenda: props.unidade.codigo_spdata_agenda,
        endereco: props.unidade.endereco,
        telefone: props.unidade.telefone,
        ativa: props.unidade.ativa
      }
    } else {
      form.value = {
        nome: '',
        codigo_spdata_centro_custo: '',
        codigo_spdata_agenda: '',
        endereco: '',
        telefone: '',
        ativa: true
      }
    }
  }
})

async function salvar() {
  if (!form.value.nome.trim()) return
  saving.value = true
  try {
    if (props.unidade) {
      const res = await unidadesStore.atualizar(props.unidade.id, form.value)
      if (res.success) {
        toast.add({ title: 'Unidade atualizada', color: 'success' })
        open.value = false
        emit('saved')
      } else {
        toast.add({ title: res.message, color: 'error' })
      }
    } else {
      const res = await unidadesStore.criar(form.value)
      if (res.success) {
        toast.add({ title: 'Unidade criada', color: 'success' })
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
  <UModal v-model:open="open">
    <template #header>
      <h2 class="text-lg font-semibold">
        {{ titulo }}
      </h2>
    </template>

    <template #body>
      <div class="space-y-4">
        <div class="space-y-1">
          <label class="text-sm font-medium">Nome</label>
          <UInput
            v-model="form.nome"
            placeholder="Nome da unidade"
          />
        </div>

        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div class="space-y-1">
            <label class="text-sm font-medium">Centro de Custo SPDATA</label>
            <UInput
              v-model="form.codigo_spdata_centro_custo"
              placeholder="Centro de Custo"
            />
          </div>
          <div class="space-y-1">
            <label class="text-sm font-medium">Agenda SPDATA</label>
            <UInput
              v-model="form.codigo_spdata_agenda"
              placeholder="Agenda"
            />
          </div>
        </div>

        <div class="space-y-1">
          <label class="text-sm font-medium">Endereco</label>
          <UInput
            v-model="form.endereco"
            placeholder="Endereco completo"
          />
        </div>

        <div class="space-y-1">
          <label class="text-sm font-medium">Telefone</label>
          <UInput
            v-model="form.telefone"
            placeholder="(00) 0000-0000"
          />
        </div>

        <div class="flex items-center gap-3">
          <USwitch v-model="form.ativa" />
          <label class="text-sm font-medium">Ativa</label>
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
          :disabled="!form.nome.trim()"
          @click="salvar"
        />
      </div>
    </template>
  </UModal>
</template>