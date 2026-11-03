<template>
  <q-dialog :model-value="modelValue" @update:model-value="$emit('update:modelValue', $event)">
    <q-card style="width: 420px; max-width: 92vw">
      <q-card-section class="bg-primary text-white">
        <div class="text-h6">{{ isEditing ? 'Renomear categoria' : 'Nova categoria' }}</div>
      </q-card-section>

      <q-card-section>
        <q-form @submit.prevent="salvar">
          <q-input
            v-model="nome"
            label="Nome da categoria"
            maxlength="60"
            outlined
            dense
            autofocus
            :rules="[(val) => (val && val.trim().length > 0) || 'Informe o nome']"
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

defineOptions({
  name: 'CategoriaFormDialog',
})

const props = defineProps({
  modelValue: { type: Boolean, required: true },
  categoria: { type: Object, default: () => ({}) },
})
const emit = defineEmits(['update:modelValue'])

const categoriasStore = useCategoriasStore()
const nome = ref('')
const loading = ref(false)

const isEditing = computed(() => !!props.categoria?.id_categoria)

watch(
  () => props.categoria,
  (categoria) => {
    nome.value = categoria?.nome ?? ''
  },
  { immediate: true },
)

async function salvar() {
  loading.value = true
  const ok = await categoriasStore.salvarCategoria({ id: props.categoria?.id_categoria, nome: nome.value.trim() })
  loading.value = false
  if (ok) emit('update:modelValue', false)
}
</script>
