<template>
  <q-dialog :model-value="modelValue" @update:model-value="$emit('update:modelValue', $event)">
    <q-card style="width: 560px; max-width: 92vw">
      <q-card-section class="bg-primary text-white">
        <div class="text-h6">{{ isEditing ? 'Editar despesa' : 'Registrar despesa manualmente' }}</div>
      </q-card-section>

      <q-card-section>
        <q-form ref="formRef" @submit.prevent="salvar">
          <DespesaCampos v-model="dados" />

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
import { useDespesasStore } from 'stores/despesas'
import DespesaCampos from 'components/DespesaCampos.vue'

defineOptions({
  name: 'DespesaFormDialog',
})

const props = defineProps({
  modelValue: { type: Boolean, required: true },
  despesa: { type: Object, default: () => ({}) },
})
const emit = defineEmits(['update:modelValue', 'despesaSalva'])

const despesasStore = useDespesasStore()
const formRef = ref(null)
const loading = ref(false)
const dados = ref({})

const isEditing = computed(() => !!props.despesa?.id_despesa)

// sempre que o diálogo recebe uma despesa, copia para o formulário
watch(
  () => props.despesa,
  (despesa) => {
    dados.value = {
      valor: despesa?.valor ?? '',
      data_despesa: despesa?.data_despesa ?? '',
      id_categoria: despesa?.categoria?.id_categoria ?? despesa?.id_categoria ?? null,
      estabelecimento: despesa?.estabelecimento ?? '',
      descricao: despesa?.descricao ?? '',
    }
  },
  { immediate: true },
)

async function salvar() {
  loading.value = true
  const payload = {
    valor: dados.value.valor,
    data_despesa: dados.value.data_despesa,
    id_categoria: dados.value.id_categoria,
    estabelecimento: dados.value.estabelecimento?.trim() || null,
    descricao: dados.value.descricao?.trim() || null,
  }
  const ok = await despesasStore.salvarDespesa(payload, props.despesa?.id_despesa)
  loading.value = false
  if (ok) {
    emit('update:modelValue', false)
    emit('despesaSalva')
  }
}
</script>
