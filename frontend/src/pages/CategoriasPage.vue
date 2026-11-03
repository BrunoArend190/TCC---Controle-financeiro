<template>
  <q-page class="q-pa-none">
    <div class="header-section text-white q-pa-md q-px-lg row items-center">
      <div class="text-h5">Categorias</div>
      <q-space />
      <q-btn label="Nova categoria" icon="add" color="white" text-color="primary" unelevated no-caps @click="abrirNova" />
    </div>

    <div class="q-pa-lg">
      <q-table
        :rows="categoriasStore.categorias"
        :columns="columns"
        row-key="id_categoria"
        :loading="categoriasStore.loading"
        flat
        bordered
        no-data-label="Nenhuma categoria encontrada."
        :rows-per-page-options="[0]"
        hide-pagination
      >
        <template #body-cell-tipo="props">
          <q-td :props="props">
            <q-badge :color="props.row.tipo === 'padrao' ? 'grey-6' : 'secondary'">
              {{ props.row.tipo === 'padrao' ? 'Padrão do sistema' : 'Personalizada' }}
            </q-badge>
          </q-td>
        </template>

        <template #body-cell-acoes="props">
          <q-td :props="props">
            <template v-if="props.row.tipo === 'personalizada'">
              <q-btn icon="edit" size="sm" flat dense color="grey-7" class="q-mr-sm" @click="abrirEdicao(props.row)">
                <q-tooltip>Renomear</q-tooltip>
              </q-btn>
              <q-btn icon="delete" size="sm" flat dense color="negative" @click="confirmarExclusao(props.row)">
                <q-tooltip>Remover</q-tooltip>
              </q-btn>
            </template>
            <span v-else class="text-caption text-grey-6">não editável (RN06)</span>
          </q-td>
        </template>
      </q-table>
    </div>

    <CategoriaFormDialog v-model="showModal" :categoria="categoriaEditando" />
  </q-page>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useQuasar } from 'quasar'
import { useCategoriasStore } from 'stores/categorias'
import CategoriaFormDialog from 'components/CategoriaFormDialog.vue'

defineOptions({
  name: 'CategoriasPage',
})

const $q = useQuasar()
const categoriasStore = useCategoriasStore()

const showModal = ref(false)
const categoriaEditando = ref({})

const columns = [
  { name: 'nome', label: 'Nome', align: 'left', field: 'nome', sortable: true },
  { name: 'tipo', label: 'Tipo', align: 'center', field: 'tipo' },
  { name: 'acoes', label: 'Ações', align: 'center', field: 'acoes' },
]

onMounted(() => categoriasStore.fetchCategorias())

function abrirNova() {
  categoriaEditando.value = {}
  showModal.value = true
}

function abrirEdicao(categoria) {
  categoriaEditando.value = categoria
  showModal.value = true
}

// RN08: despesas e recorrentes vão para "Não categorizado" e o orçamento da categoria é excluído
function confirmarExclusao(categoria) {
  $q.dialog({
    title: 'Confirmação',
    message: `Remover "${categoria.nome}"? As despesas e recorrências dela passarão para "Não categorizado" e o orçamento dela será excluído.`,
    cancel: { label: 'Cancelar', flat: true },
    ok: { label: 'Remover', color: 'negative', unelevated: true },
    persistent: true,
  }).onOk(() => categoriasStore.deleteCategoria(categoria.id_categoria))
}
</script>
