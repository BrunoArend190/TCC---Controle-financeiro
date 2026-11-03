<template>
  <q-dialog :model-value="modelValue" @update:model-value="$emit('update:modelValue', $event)">
    <q-card style="width: 460px; max-width: 92vw">
      <q-card-section class="bg-primary text-white">
        <div class="text-h6">{{ isEditing ? 'Alterar orçamento' : 'Novo orçamento' }}</div>
      </q-card-section>

      <q-card-section>
        <q-form @submit.prevent="salvar">
          <q-select
            v-model="idCategoria"
            :options="opcoesCategoria"
            :disable="isEditing"
            label="Categoria *"
            emit-value
            map-options
            outlined
            dense
            :rules="[(val) => !!val || 'Selecione a categoria']"
          />
          <q-input
            v-model="valorLimite"
            label="Limite mensal (R$) *"
            type="number"
            step="0.01"
            min="0.01"
            outlined
            dense
            hint="O limite vale para todos os meses"
            :rules="[(val) => Number(val) > 0 || 'O limite deve ser maior que zero']"
          />

          <q-card-actions align="right" class="q-mt-md q-px-none">
            <q-btn label="Cancelar" color="grey" flat @click="$emit('update:modelValue', false)" />
            <q-btn label="Salvar" color="primary" type="submit" unelevated :loading="loading" />
          </q-card-actions>
        </q-form>
      </q-card-section>
    </q-card>
  </q-dialog>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { useCategoriasStore } from 'stores/categorias'
import { useOrcamentosStore } from 'stores/orcamentos'

defineOptions({
  name: 'OrcamentoFormDialog',
})

const props = defineProps({
  modelValue: { type: Boolean, required: true },
  orcamento: { type: Object, default: () => ({}) },
})
const emit = defineEmits(['update:modelValue'])

const categoriasStore = useCategoriasStore()
const orcamentosStore = useOrcamentosStore()

const idCategoria = ref(null)
const valorLimite = ref('')
const loading = ref(false)

const isEditing = computed(() => !!props.orcamento?.id_orcamento)

// no cadastro, só aparecem as categorias que ainda não têm orçamento
const opcoesCategoria = computed(() => {
  if (isEditing.value) return categoriasStore.opcoes
  const usadas = orcamentosStore.orcamentos.map((o) => o.categoria.id_categoria)
  return categoriasStore.opcoes.filter((c) => !usadas.includes(c.value))
})

watch(
  () => props.orcamento,
  (orcamento) => {
    idCategoria.value = orcamento?.categoria?.id_categoria ?? null
    valorLimite.value = orcamento?.valor_limite ?? ''
  },
  { immediate: true },
)

async function salvar() {
  loading.value = true
  const ok = await orcamentosStore.salvarOrcamento(idCategoria.value, valorLimite.value)
  loading.value = false
  if (ok) emit('update:modelValue', false)
}
</script>
