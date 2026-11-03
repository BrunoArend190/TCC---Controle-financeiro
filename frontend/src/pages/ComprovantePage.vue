<template>
  <q-page class="q-pa-none">
    <div class="header-section text-white q-pa-md q-px-lg row items-center">
      <div>
        <div class="text-h5">Registrar despesa por comprovante</div>
        <div class="text-caption text-blue-2">Os dados são extraídos automaticamente pelo NuExtract3</div>
      </div>
    </div>

    <div class="q-pa-lg">
      <!-- Etapa 1: envio do arquivo -->
      <q-card flat bordered class="q-mb-lg">
        <q-card-section class="row items-center q-col-gutter-md">
          <div class="col-12 col-md">
            <q-file
              v-model="arquivo"
              label="Foto ou PDF da nota fiscal / recibo"
              accept=".jpg,.jpeg,.png,.pdf"
              max-file-size="10485760"
              outlined
              dense
              clearable
              @rejected="arquivoRejeitado"
              @update:model-value="limparResultado"
            >
              <template #prepend><q-icon name="attach_file" /></template>
            </q-file>
          </div>
          <div class="col-12 col-md-auto">
            <q-btn
              label="Extrair dados"
              icon="auto_awesome"
              color="primary"
              unelevated
              no-caps
              :disable="!arquivo"
              :loading="processando"
              @click="extrair"
            />
          </div>
        </q-card-section>
        <q-card-section v-if="processando" class="q-pt-none">
          <q-linear-progress indeterminate color="secondary" />
          <div class="text-caption text-grey-7 q-mt-sm">
            Lendo o comprovante… na primeira leitura o modelo é carregado na GPU e pode levar até 1 minuto.
          </div>
        </q-card-section>
      </q-card>

      <!-- Etapa 2: conferência e correção (UC07) -->
      <div v-if="resultado" class="row q-col-gutter-lg">
        <div v-if="previa" class="col-12 col-md-5">
          <q-card flat bordered>
            <q-img :src="previa" fit="contain" style="max-height: 560px" />
          </q-card>
        </div>

        <div class="col-12" :class="{ 'col-md-7': previa }">
          <q-card flat bordered>
            <q-card-section>
              <q-banner dense rounded :class="banner.classe" class="q-mb-md">
                <template #avatar><q-icon :name="banner.icone" /></template>
                <div class="text-weight-medium">{{ banner.titulo }} · campos preenchidos: {{ confiancaPct }}%</div>
                <div v-if="resultado.mensagem" class="text-caption">{{ resultado.mensagem }}</div>
              </q-banner>
              <div class="text-caption text-grey-7 q-mb-md">
                Confira os dados abaixo e corrija o que for necessário antes de salvar.
              </div>

              <q-form @submit.prevent="confirmar">
                <DespesaCampos v-model="dados" :destaque="destaque" />

                <div class="row justify-end q-gutter-sm q-mt-md">
                  <q-btn label="Cancelar" color="grey" flat no-caps @click="cancelar" />
                  <q-btn label="Confirmar e salvar" icon="check" color="primary" type="submit" unelevated no-caps :loading="salvando" />
                </div>
              </q-form>
            </q-card-section>
          </q-card>
        </div>
      </div>
    </div>
  </q-page>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { Notify } from 'quasar'
import { useDespesasStore } from 'stores/despesas'
import DespesaCampos from 'components/DespesaCampos.vue'

defineOptions({
  name: 'ComprovantePage',
})

const router = useRouter()
const despesasStore = useDespesasStore()

const arquivo = ref(null)
const previa = ref('')
const resultado = ref(null)
const dados = ref({})
const processando = ref(false)
const salvando = ref(false)

const BANNERS = {
  sucesso: { titulo: 'Leitura concluída', icone: 'check_circle', classe: 'bg-green-1 text-green-9' },
  falha_parcial: { titulo: 'Leitura parcial', icone: 'warning', classe: 'bg-orange-1 text-orange-9' },
  falha_total: { titulo: 'Não foi possível ler o comprovante', icone: 'error', classe: 'bg-red-1 text-red-9' },
}
const banner = computed(() => BANNERS[resultado.value?.status] ?? BANNERS.falha_total)
const confiancaPct = computed(() => Math.round(Number(resultado.value?.confianca ?? 0) * 100))

// campos que o modelo não conseguiu preencher ficam destacados
const destaque = computed(() => {
  const d = resultado.value?.dados ?? {}
  return {
    valor: !d.valor,
    data_despesa: !d.data_despesa,
    estabelecimento: !d.estabelecimento,
    id_categoria: !d.id_categoria_sugerida,
  }
})

function limparResultado(f) {
  resultado.value = null
  previa.value = f && f.type.startsWith('image/') ? URL.createObjectURL(f) : ''
}

function arquivoRejeitado() {
  Notify.create({ type: 'warning', message: 'Envie um arquivo JPG, PNG ou PDF de até 10 MB.' })
}

// Etapa 1: envia ao backend, que chama o NuExtract3
async function extrair() {
  processando.value = true
  try {
    resultado.value = await despesasStore.extrairComprovante(arquivo.value)
    const d = resultado.value.dados
    dados.value = {
      valor: d.valor ?? '',
      data_despesa: d.data_despesa ?? '',
      id_categoria: d.id_categoria_sugerida,
      estabelecimento: d.estabelecimento ?? '',
      descricao: '',
    }
  } catch (error) {
    Notify.create({ type: 'negative', message: error.message })
  } finally {
    processando.value = false
  }
}

// Etapa 2: grava a despesa com os dados conferidos
async function confirmar() {
  salvando.value = true
  const ok = await despesasStore.confirmarComprovante({
    id_upload: resultado.value.id_upload,
    valor: dados.value.valor,
    data_despesa: dados.value.data_despesa,
    id_categoria: dados.value.id_categoria,
    estabelecimento: dados.value.estabelecimento?.trim() || null,
    descricao: dados.value.descricao?.trim() || null,
  })
  salvando.value = false
  if (ok) router.push('/app/despesas')
}

function cancelar() {
  arquivo.value = null
  limparResultado(null)
}
</script>
