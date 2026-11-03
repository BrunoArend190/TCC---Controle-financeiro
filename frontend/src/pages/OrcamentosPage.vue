<template>
  <q-page class="q-pa-none">
    <div class="header-section text-white q-pa-md q-px-lg row items-center q-gutter-sm">
      <div class="text-h5">Orçamentos</div>
      <q-space />
      <q-input
        v-model="orcamentosStore.mes"
        label="Mês"
        type="month"
        stack-label
        dense
        filled
        bg-color="white"
        style="width: 170px"
      />
      <q-btn label="Novo orçamento" icon="add" color="white" text-color="primary" unelevated no-caps @click="abrirNovo" />
    </div>

    <div class="q-pa-lg">
      <div v-if="orcamentosStore.orcamentos.length" class="text-subtitle1 q-mb-md">
        Gasto nas categorias com orçamento:
        <strong>{{ formatarMoeda(orcamentosStore.totalGasto) }}</strong>
        de {{ formatarMoeda(orcamentosStore.totalLimite) }}
      </div>

      <div v-else-if="!orcamentosStore.loading" class="text-center text-grey-7 q-pa-xl">
        <q-icon name="savings" size="64px" color="grey-5" />
        <div class="text-subtitle1 q-mt-md">Defina limites mensais para acompanhar seus gastos por categoria.</div>
      </div>

      <div class="row q-col-gutter-md">
        <div v-for="o in orcamentosStore.orcamentos" :key="o.id_orcamento" class="col-12 col-md-6">
          <q-card flat bordered>
            <q-card-section>
              <div class="row items-center no-wrap q-mb-sm">
                <div class="text-subtitle1 text-weight-medium ellipsis">{{ o.categoria.nome }}</div>
                <q-badge :color="SITUACAO[o.situacao].cor" class="q-ml-sm">{{ SITUACAO[o.situacao].label }}</q-badge>
                <q-space />
                <q-btn icon="edit" size="sm" flat dense color="grey-7" @click="abrirEdicao(o)">
                  <q-tooltip>Alterar limite</q-tooltip>
                </q-btn>
                <q-btn icon="delete" size="sm" flat dense color="negative" @click="confirmarExclusao(o)">
                  <q-tooltip>Remover</q-tooltip>
                </q-btn>
              </div>

              <q-linear-progress
                :value="Math.min(o.percentual / 100, 1)"
                :color="SITUACAO[o.situacao].cor"
                track-color="grey-3"
                size="12px"
                rounded
              />

              <div class="row q-mt-sm text-body2">
                <div>{{ formatarMoeda(o.gasto) }} de {{ formatarMoeda(o.valor_limite) }} ({{ formatarPercentual(o.percentual) }})</div>
                <q-space />
                <div :class="Number(o.restante) < 0 ? 'text-negative text-weight-medium' : 'text-grey-7'">
                  {{ Number(o.restante) < 0 ? 'Excedeu ' + formatarMoeda(-o.restante) : 'Restam ' + formatarMoeda(o.restante) }}
                </div>
              </div>
            </q-card-section>
          </q-card>
        </div>
      </div>
    </div>

    <OrcamentoFormDialog v-model="showModal" :orcamento="orcamentoEditando" />
  </q-page>
</template>

<script setup>
import { ref, watch, onMounted } from 'vue'
import { useQuasar } from 'quasar'
import { useOrcamentosStore } from 'stores/orcamentos'
import { useCategoriasStore } from 'stores/categorias'
import OrcamentoFormDialog from 'components/OrcamentoFormDialog.vue'
import { formatarMoeda, formatarPercentual, SITUACAO_ORCAMENTO as SITUACAO } from 'src/utils/formatadores'

defineOptions({
  name: 'OrcamentosPage',
})

const $q = useQuasar()
const orcamentosStore = useOrcamentosStore()
const categoriasStore = useCategoriasStore()

const showModal = ref(false)
const orcamentoEditando = ref({})

onMounted(() => {
  orcamentosStore.fetchOrcamentos()
  if (categoriasStore.categorias.length === 0) categoriasStore.fetchCategorias()
})

// limpar o campo de mês não deve fazer a tela consultar um período inválido
watch(
  () => orcamentosStore.mes,
  (mes) => {
    if (mes) orcamentosStore.fetchOrcamentos()
  },
)

function abrirNovo() {
  orcamentoEditando.value = {}
  showModal.value = true
}

function abrirEdicao(orcamento) {
  orcamentoEditando.value = orcamento
  showModal.value = true
}

function confirmarExclusao(orcamento) {
  $q.dialog({
    title: 'Confirmação',
    message: `Remover o orçamento de "${orcamento.categoria.nome}"? As despesas não serão afetadas.`,
    cancel: { label: 'Cancelar', flat: true },
    ok: { label: 'Remover', color: 'negative', unelevated: true },
    persistent: true,
  }).onOk(() => orcamentosStore.deleteOrcamento(orcamento.categoria.id_categoria))
}
</script>
