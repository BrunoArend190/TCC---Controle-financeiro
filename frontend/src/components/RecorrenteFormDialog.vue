<template>
  <q-dialog :model-value="modelValue" @update:model-value="$emit('update:modelValue', $event)">
    <q-card style="width: 560px; max-width: 92vw">
      <q-card-section class="bg-primary text-white">
        <div class="text-h6">{{ isEditing ? 'Editar despesa recorrente' : 'Nova despesa recorrente' }}</div>
      </q-card-section>

      <q-card-section>
        <q-form @submit.prevent="salvar">
          <div class="row q-col-gutter-md">
            <div class="col-12 col-sm-6">
              <q-input
                v-model="dados.valor"
                label="Valor (R$) *"
                type="number"
                step="0.01"
                min="0.01"
                outlined
                dense
                :rules="[(val) => Number(val) > 0 || 'O valor deve ser maior que zero']"
              />
            </div>
            <div class="col-12 col-sm-6">
              <q-input
                v-model.number="dados.dia_lancamento"
                label="Dia do lançamento *"
                type="number"
                min="1"
                max="31"
                outlined
                dense
                hint="Em meses mais curtos, usa o último dia"
                :rules="[(val) => (Number.isInteger(val) && val >= 1 && val <= 31) || 'Informe um dia de 1 a 31']"
              />
            </div>
          </div>

          <q-select
            v-model="dados.id_categoria"
            :options="categoriasStore.opcoes"
            label="Categoria *"
            emit-value
            map-options
            outlined
            dense
            class="q-mt-sm"
            :rules="[(val) => !!val || 'Selecione a categoria']"
          />
          <q-input
            v-model="dados.estabelecimento"
            label="Estabelecimento (ex.: Netflix, imobiliária)"
            maxlength="150"
            outlined
            dense
            class="q-mb-md"
          />
          <q-input v-model="dados.descricao" label="Descrição" maxlength="255" outlined dense />

          <div v-if="isEditing" class="text-caption text-grey-7 q-mt-md">
            As alterações valem para os próximos lançamentos; as despesas já lançadas não mudam.
          </div>

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
import { useRecorrentesStore } from 'stores/recorrentes'

defineOptions({
  name: 'RecorrenteFormDialog',
})

const props = defineProps({
  modelValue: { type: Boolean, required: true },
  recorrente: { type: Object, default: () => ({}) },
})
const emit = defineEmits(['update:modelValue'])

const categoriasStore = useCategoriasStore()
const recorrentesStore = useRecorrentesStore()

const dados = ref({})
const loading = ref(false)

const isEditing = computed(() => !!props.recorrente?.id_recorrente)

watch(
  () => props.recorrente,
  (r) => {
    dados.value = {
      valor: r?.valor ?? '',
      dia_lancamento: r?.dia_lancamento ?? null,
      id_categoria: r?.categoria?.id_categoria ?? null,
      estabelecimento: r?.estabelecimento ?? '',
      descricao: r?.descricao ?? '',
      ativa: r?.ativa ?? true,
    }
  },
  { immediate: true },
)

async function salvar() {
  loading.value = true
  const ok = await recorrentesStore.salvarRecorrente(dados.value, props.recorrente?.id_recorrente)
  loading.value = false
  if (ok) emit('update:modelValue', false)
}
</script>
