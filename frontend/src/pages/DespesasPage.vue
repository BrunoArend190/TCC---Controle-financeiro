<template>
  <q-page class="q-pa-none">
    <div class="header-section text-white q-pa-md q-px-lg row items-center q-gutter-sm">
      <div class="text-h5">Despesas</div>
      <q-space />
      <q-btn label="Nova despesa" icon="add" color="white" text-color="primary" unelevated no-caps @click="abrirNova" />
      <q-btn
        label="Enviar comprovante"
        icon="document_scanner"
        color="secondary"
        unelevated
        no-caps
        to="/app/comprovante"
      />
    </div>

    <div class="q-pa-lg">
      <!-- Filtros (RF10) -->
      <div class="row q-col-gutter-md q-mb-md">
        <div class="col-6 col-md-2">
          <q-input v-model="despesasStore.filtros.data_inicio" label="De" type="date" stack-label outlined dense bg-color="white" />
        </div>
        <div class="col-6 col-md-2">
          <q-input v-model="despesasStore.filtros.data_fim" label="Até" type="date" stack-label outlined dense bg-color="white" />
        </div>
        <div class="col-12 col-md-3">
          <q-select
            v-model="despesasStore.filtros.id_categoria"
            :options="categoriasStore.opcoes"
            label="Categoria"
            emit-value
            map-options
            clearable
            outlined
            dense
            bg-color="white"
          />
        </div>
        <div class="col-12 col-md-5">
          <q-input
            v-model="despesasStore.filtros.busca"
            label="Buscar estabelecimento ou descrição"
            debounce="400"
            clearable
            outlined
            dense
            bg-color="white"
          >
            <template #prepend><q-icon name="search" /></template>
          </q-input>
        </div>
      </div>

      <q-table
        :rows="despesasStore.despesas"
        :columns="columns"
        row-key="id_despesa"
        :loading="despesasStore.loading"
        flat
        bordered
        no-data-label="Nenhuma despesa encontrada."
        :rows-per-page-options="[10, 20, 50]"
        :pagination="{ rowsPerPage: 10 }"
      >
        <template #body-cell-estabelecimento="props">
          <q-td :props="props">
            <div>{{ props.row.estabelecimento || '—' }}</div>
            <div v-if="props.row.descricao" class="text-caption text-grey-7">{{ props.row.descricao }}</div>
          </q-td>
        </template>

        <template #body-cell-status="props">
          <q-td :props="props">
            <q-badge :color="STATUS_DESPESA[props.row.status_extracao].cor">
              {{ STATUS_DESPESA[props.row.status_extracao].label }}
            </q-badge>
          </q-td>
        </template>

        <template #body-cell-acoes="props">
          <q-td :props="props">
            <q-btn
              v-if="props.row.possui_comprovante"
              icon="image"
              size="sm"
              flat
              dense
              color="secondary"
              @click="despesasStore.abrirComprovante(props.row.id_despesa)"
            >
              <q-tooltip>Ver comprovante</q-tooltip>
            </q-btn>
            <q-btn icon="edit" size="sm" flat dense color="grey-7" class="q-mx-xs" @click="abrirEdicao(props.row)">
              <q-tooltip>Editar</q-tooltip>
            </q-btn>
            <q-btn icon="delete" size="sm" flat dense color="negative" @click="confirmarExclusao(props.row)">
              <q-tooltip>Excluir</q-tooltip>
            </q-btn>
          </q-td>
        </template>

        <template #bottom-row>
          <q-tr v-if="despesasStore.despesas.length">
            <q-td colspan="3" class="text-weight-bold">Total ({{ despesasStore.despesas.length }} {{ despesasStore.despesas.length === 1 ? 'despesa' : 'despesas' }})</q-td>
            <q-td class="text-right text-weight-bold">{{ formatarMoeda(despesasStore.total) }}</q-td>
            <q-td colspan="2" />
          </q-tr>
        </template>
      </q-table>
    </div>

    <DespesaFormDialog v-model="showModal" :despesa="despesaEditando" />
  </q-page>
</template>

<script setup>
import { ref, watch, onMounted } from 'vue'
import { useQuasar } from 'quasar'
import { useDespesasStore } from 'stores/despesas'
import { useCategoriasStore } from 'stores/categorias'
import DespesaFormDialog from 'components/DespesaFormDialog.vue'
import { formatarMoeda, formatarData, hojeISO, STATUS_DESPESA } from 'src/utils/formatadores'

defineOptions({
  name: 'DespesasPage',
})

const $q = useQuasar()
const despesasStore = useDespesasStore()
const categoriasStore = useCategoriasStore()

const showModal = ref(false)
const despesaEditando = ref({})

const columns = [
  { name: 'data', label: 'Data', align: 'left', field: 'data_despesa', format: formatarData, sortable: true },
  { name: 'estabelecimento', label: 'Estabelecimento', align: 'left', field: 'estabelecimento' },
  { name: 'categoria', label: 'Categoria', align: 'left', field: (row) => row.categoria.nome, sortable: true },
  { name: 'valor', label: 'Valor', align: 'right', field: 'valor', format: formatarMoeda, sortable: true, sort: (a, b) => a - b },
  { name: 'status', label: 'Origem', align: 'center', field: 'status_extracao' },
  { name: 'acoes', label: 'Ações', align: 'center', field: 'acoes' },
]

// READ: carrega ao abrir a tela e sempre que um filtro muda
onMounted(() => {
  despesasStore.fetchDespesas()
  if (categoriasStore.categorias.length === 0) categoriasStore.fetchCategorias()
})
watch(() => ({ ...despesasStore.filtros }), () => despesasStore.fetchDespesas())

// CREATE & UPDATE: abrem o diálogo
function abrirNova() {
  despesaEditando.value = { data_despesa: hojeISO() }
  showModal.value = true
}

function abrirEdicao(despesa) {
  despesaEditando.value = despesa
  showModal.value = true
}

// DELETE com confirmação
function confirmarExclusao(despesa) {
  $q.dialog({
    title: 'Confirmação',
    message: `Excluir a despesa de ${formatarMoeda(despesa.valor)} em ${formatarData(despesa.data_despesa)}?`,
    cancel: { label: 'Cancelar', flat: true },
    ok: { label: 'Excluir', color: 'negative', unelevated: true },
    persistent: true,
  }).onOk(() => despesasStore.deleteDespesa(despesa.id_despesa))
}
</script>
