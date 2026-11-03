<template>
  <q-page class="q-pa-none">
    <div class="header-section text-white q-pa-md q-px-lg row items-center q-col-gutter-md">
      <div class="text-h5 col-12 col-md">Dashboard</div>
      <div class="col-6 col-md-auto">
        <q-input v-model="relatoriosStore.filtros.data_inicio" label="De" type="date" stack-label dense filled bg-color="white" />
      </div>
      <div class="col-6 col-md-auto">
        <q-input v-model="relatoriosStore.filtros.data_fim" label="Até" type="date" stack-label dense filled bg-color="white" />
      </div>
    </div>

    <div class="q-pa-lg">
      <q-inner-loading :showing="relatoriosStore.loading && !resumo" />

      <template v-if="resumo">
        <!-- Indicadores -->
        <div class="row q-col-gutter-md q-mb-lg">
          <div v-for="card in indicadores" :key="card.titulo" class="col-12 col-sm-4">
            <q-card flat bordered>
              <q-card-section class="row items-center no-wrap">
                <q-avatar :icon="card.icone" color="blue-1" text-color="primary" size="52px" class="q-mr-md" />
                <div>
                  <div class="text-caption text-grey-7">{{ card.titulo }}</div>
                  <div class="text-h5 text-primary text-weight-medium">{{ card.valor }}</div>
                </div>
              </q-card-section>
            </q-card>
          </div>
        </div>

        <!-- Alertas de orçamento do mês atual (RN17) -->
        <div v-if="orcamentosStore.emAtencao.length" class="q-mb-lg">
          <q-banner
            v-for="o in orcamentosStore.emAtencao"
            :key="o.id_orcamento"
            dense
            rounded
            class="q-mb-sm"
            :class="o.situacao === 'excedido' ? 'bg-red-1 text-red-9' : 'bg-orange-1 text-orange-9'"
          >
            <template #avatar>
              <q-icon :name="o.situacao === 'excedido' ? 'error' : 'warning'" />
            </template>
            <span class="text-weight-medium">{{ o.categoria.nome }}:</span>
            {{ formatarMoeda(o.gasto) }} de {{ formatarMoeda(o.valor_limite) }} ({{ formatarPercentual(o.percentual) }} do orçamento deste mês)
            <template #action>
              <q-btn flat dense no-caps label="Ver orçamentos" to="/app/orcamentos" />
            </template>
          </q-banner>
        </div>

        <!-- Comparativo com o mês anterior -->
        <q-card v-if="relatoriosStore.comparativo?.frases.length" flat bordered class="q-mb-lg">
          <q-card-section>
            <div class="text-subtitle1 text-weight-medium q-mb-sm">Comparado ao mês passado</div>
            <div
              v-for="frase in relatoriosStore.comparativo.frases"
              :key="frase.texto"
              class="row items-start no-wrap q-mb-xs"
            >
              <q-icon
                :name="frase.tipo === 'aumento' ? 'trending_up' : 'trending_down'"
                :color="frase.tipo === 'aumento' ? 'negative' : 'positive'"
                size="20px"
                class="q-mr-sm q-mt-xs"
              />
              <div class="text-body2 q-mt-xs">{{ frase.texto }}</div>
            </div>
          </q-card-section>
        </q-card>

        <div v-if="resumo.quantidade === 0" class="text-center text-grey-7 q-pa-xl">
          <q-icon name="insights" size="64px" color="grey-5" />
          <div class="text-subtitle1 q-mt-md">Nenhuma despesa no período.</div>
          <q-btn class="q-mt-md" label="Registrar despesa" color="primary" unelevated no-caps to="/app/despesas" />
        </div>

        <!-- Gráficos (RF14) -->
        <div v-else class="row q-col-gutter-md">
          <div class="col-12 col-md-5">
            <q-card flat bordered>
              <q-card-section>
                <div class="text-subtitle1 text-weight-medium q-mb-md">Gastos por categoria</div>
                <div class="grafico"><Doughnut :data="dadosCategoria" :options="opcoesCategoria" /></div>
              </q-card-section>
            </q-card>
          </div>
          <div class="col-12 col-md-7">
            <q-card flat bordered>
              <q-card-section>
                <div class="text-subtitle1 text-weight-medium q-mb-md">Gastos por mês</div>
                <div class="grafico"><Bar :data="dadosMes" :options="opcoesMes" /></div>
              </q-card-section>
            </q-card>
          </div>
        </div>
      </template>
    </div>
  </q-page>
</template>

<script setup>
import { computed, watch, onMounted } from 'vue'
import { Doughnut, Bar } from 'vue-chartjs'
import { Chart as ChartJS, ArcElement, BarElement, CategoryScale, LinearScale, Tooltip, Legend } from 'chart.js'
import { useRelatoriosStore } from 'stores/relatorios'
import { useOrcamentosStore } from 'stores/orcamentos'
import { formatarMoeda, formatarPercentual, hojeISO } from 'src/utils/formatadores'

ChartJS.register(ArcElement, BarElement, CategoryScale, LinearScale, Tooltip, Legend)

defineOptions({
  name: 'IndexPage',
})

const relatoriosStore = useRelatoriosStore()
const orcamentosStore = useOrcamentosStore()
const resumo = computed(() => relatoriosStore.resumo)

const CORES = ['#0d4580', '#2a7ab8', '#4fa3d9', '#e08a2c', '#6a9e3f', '#b0473a', '#7a5ca8', '#8a8f98']

const indicadores = computed(() => [
  { titulo: 'Total gasto', valor: formatarMoeda(resumo.value.total), icone: 'payments' },
  { titulo: 'Despesas registradas', valor: resumo.value.quantidade, icone: 'receipt_long' },
  { titulo: 'Maior categoria', valor: relatoriosStore.maiorCategoria, icone: 'category' },
])

const dadosCategoria = computed(() => ({
  labels: resumo.value.por_categoria.map((c) => c.categoria),
  datasets: [
    {
      data: resumo.value.por_categoria.map((c) => Number(c.total)),
      backgroundColor: resumo.value.por_categoria.map((_, i) => CORES[i % CORES.length]),
    },
  ],
}))

const dadosMes = computed(() => ({
  labels: resumo.value.por_mes.map((m) => m.mes.split('-').reverse().join('/')),
  datasets: [{ label: 'Total', data: resumo.value.por_mes.map((m) => Number(m.total)), backgroundColor: '#0d4580', borderRadius: 4, maxBarThickness: 64 }],
}))

const tooltipMoeda = { callbacks: { label: (ctx) => ` ${formatarMoeda(ctx.parsed.y ?? ctx.parsed)}` } }
const opcoesCategoria = { responsive: true, maintainAspectRatio: false, plugins: { tooltip: tooltipMoeda, legend: { position: 'bottom' } } }
const opcoesMes = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: { tooltip: tooltipMoeda, legend: { display: false } },
  scales: { y: { ticks: { callback: (v) => formatarMoeda(v) } } },
}

onMounted(() => {
  relatoriosStore.fetchResumo()
  relatoriosStore.fetchComparativo()
  // os alertas sempre se referem ao mês atual, mesmo que outro mês tenha sido aberto na tela de Orçamentos
  orcamentosStore.mes = hojeISO().slice(0, 7)
  orcamentosStore.fetchOrcamentos()
})
watch(() => ({ ...relatoriosStore.filtros }), () => relatoriosStore.fetchResumo())
</script>

<style lang="scss" scoped>
.grafico {
  height: 300px;
  position: relative;
}
</style>
