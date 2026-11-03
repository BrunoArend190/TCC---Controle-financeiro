<template>
  <div>
    <div class="row q-col-gutter-md">
      <div class="col-12 col-sm-6">
        <q-input
          :model-value="modelValue.valor"
          @update:model-value="(v) => alterar('valor', v)"
          label="Valor (R$) *"
          type="number"
          step="0.01"
          min="0.01"
          outlined
          dense
          :class="{ 'campo-destaque': destaque.valor }"
          :rules="[(val) => Number(val) > 0 || 'O valor deve ser maior que zero (RN03)']"
        />
      </div>
      <div class="col-12 col-sm-6">
        <q-input
          :model-value="modelValue.data_despesa"
          @update:model-value="(v) => alterar('data_despesa', v)"
          label="Data *"
          type="date"
          stack-label
          :max="hoje"
          outlined
          dense
          :class="{ 'campo-destaque': destaque.data_despesa }"
          :rules="[
            (val) => !!val || 'Informe a data',
            (val) => val <= hoje || 'A data não pode ser futura (RN04)',
          ]"
        />
      </div>
    </div>

    <q-select
      :model-value="modelValue.id_categoria"
      @update:model-value="(v) => alterar('id_categoria', v)"
      :options="categoriasStore.opcoes"
      label="Categoria *"
      emit-value
      map-options
      outlined
      dense
      :class="{ 'campo-destaque': destaque.id_categoria }"
      :rules="[(val) => !!val || 'Selecione a categoria (RN05)']"
    />

    <q-input
      :model-value="modelValue.estabelecimento"
      @update:model-value="(v) => alterar('estabelecimento', v)"
      label="Estabelecimento"
      maxlength="150"
      outlined
      dense
      class="q-mb-md"
      :class="{ 'campo-destaque': destaque.estabelecimento }"
    />

    <q-input
      :model-value="modelValue.descricao"
      @update:model-value="(v) => alterar('descricao', v)"
      label="Descrição"
      maxlength="255"
      outlined
      dense
    />
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import { useCategoriasStore } from 'stores/categorias'
import { hojeISO } from 'src/utils/formatadores'

defineOptions({
  name: 'DespesaCampos',
})

// v-model="dados": o pai é dono do objeto; aqui só emitimos a versão alterada
const props = defineProps({
  modelValue: { type: Object, required: true },
  // campos a destacar (ex.: os que o NuExtract3 não preencheu)
  destaque: { type: Object, default: () => ({}) },
})
const emit = defineEmits(['update:modelValue'])

const categoriasStore = useCategoriasStore()
const hoje = hojeISO()

function alterar(campo, valor) {
  emit('update:modelValue', { ...props.modelValue, [campo]: valor })
}

onMounted(() => {
  if (categoriasStore.categorias.length === 0) categoriasStore.fetchCategorias()
})
</script>
