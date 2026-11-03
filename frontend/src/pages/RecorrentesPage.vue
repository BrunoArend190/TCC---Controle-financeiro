<template>
  <q-page class="q-pa-none">
    <div class="header-section text-white q-pa-md q-px-lg row items-center">
      <div>
        <div class="text-h5">Despesas recorrentes</div>
        <div class="text-caption text-blue-2">Aluguel, assinaturas e outras contas lançadas automaticamente todo mês</div>
      </div>
      <q-space />
      <q-btn label="Nova recorrente" icon="add" color="white" text-color="primary" unelevated no-caps @click="abrirNova" />
    </div>

    <div class="q-pa-lg">
      <div v-if="recorrentesStore.recorrentes.length" class="text-subtitle1 q-mb-md">
        Compromisso mensal: <strong>{{ formatarMoeda(recorrentesStore.totalMensal) }}</strong>
      </div>

      <q-table
        :rows="recorrentesStore.recorrentes"
        :columns="columns"
        row-key="id_recorrente"
        :loading="recorrentesStore.loading"
        flat
        bordered
        no-data-label="Nenhuma despesa recorrente cadastrada."
        :rows-per-page-options="[0]"
        hide-pagination
      >
        <template #body-cell-estabelecimento="props">
          <q-td :props="props">
            <div>{{ props.row.estabelecimento || '—' }}</div>
            <div v-if="props.row.descricao" class="text-caption text-grey-7">{{ props.row.descricao }}</div>
          </q-td>
        </template>

        <template #body-cell-proximo="props">
          <q-td :props="props">
            <span v-if="props.row.ativa">{{ formatarData(props.row.proximo_lancamento) }}</span>
            <q-badge v-else color="grey-6">Pausada</q-badge>
          </q-td>
        </template>

        <template #body-cell-ativa="props">
          <q-td :props="props">
            <q-toggle
              :model-value="props.row.ativa"
              color="secondary"
              dense
              :aria-label="props.row.ativa ? 'Pausar lançamentos' : 'Reativar lançamentos'"
              @update:model-value="(ativa) => recorrentesStore.alternarAtiva(props.row, ativa)"
            />
          </q-td>
        </template>

        <template #body-cell-acoes="props">
          <q-td :props="props">
            <q-btn icon="edit" size="sm" flat dense color="grey-7" class="q-mr-xs" @click="abrirEdicao(props.row)">
              <q-tooltip>Editar</q-tooltip>
            </q-btn>
            <q-btn icon="delete" size="sm" flat dense color="negative" @click="confirmarExclusao(props.row)">
              <q-tooltip>Encerrar</q-tooltip>
            </q-btn>
          </q-td>
        </template>
      </q-table>
    </div>

    <RecorrenteFormDialog v-model="showModal" :recorrente="recorrenteEditando" />
  </q-page>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useQuasar } from 'quasar'
import { useRecorrentesStore } from 'stores/recorrentes'
import { useCategoriasStore } from 'stores/categorias'
import RecorrenteFormDialog from 'components/RecorrenteFormDialog.vue'
import { formatarMoeda, formatarData } from 'src/utils/formatadores'

defineOptions({
  name: 'RecorrentesPage',
})

const $q = useQuasar()
const recorrentesStore = useRecorrentesStore()
const categoriasStore = useCategoriasStore()

const showModal = ref(false)
const recorrenteEditando = ref({})

const columns = [
  { name: 'estabelecimento', label: 'Estabelecimento', align: 'left', field: 'estabelecimento' },
  { name: 'categoria', label: 'Categoria', align: 'left', field: (row) => row.categoria.nome },
  { name: 'valor', label: 'Valor', align: 'right', field: 'valor', format: formatarMoeda },
  { name: 'dia', label: 'Dia', align: 'center', field: 'dia_lancamento' },
  { name: 'proximo', label: 'Próximo lançamento', align: 'center', field: 'proximo_lancamento' },
  { name: 'ativa', label: 'Ativa', align: 'center', field: 'ativa' },
  { name: 'acoes', label: 'Ações', align: 'center', field: 'acoes' },
]

onMounted(() => {
  recorrentesStore.fetchRecorrentes()
  if (categoriasStore.categorias.length === 0) categoriasStore.fetchCategorias()
})

function abrirNova() {
  recorrenteEditando.value = {}
  showModal.value = true
}

function abrirEdicao(recorrente) {
  recorrenteEditando.value = recorrente
  showModal.value = true
}

function confirmarExclusao(recorrente) {
  $q.dialog({
    title: 'Confirmação',
    message: `Encerrar "${recorrente.estabelecimento || recorrente.categoria.nome}"? As despesas já lançadas serão mantidas.`,
    cancel: { label: 'Cancelar', flat: true },
    ok: { label: 'Encerrar', color: 'negative', unelevated: true },
    persistent: true,
  }).onOk(() => recorrentesStore.deleteRecorrente(recorrente.id_recorrente))
}
</script>
