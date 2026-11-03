import { defineStore, acceptHMRUpdate } from 'pinia'
import { Notify } from 'quasar'
import relatorioService from 'src/services/relatorioService'
import { mensagemErro } from 'boot/axios'

const primeiroDiaDoAno = () => `${new Date().getFullYear()}-01-01`

export const useRelatoriosStore = defineStore('relatorios', {
  state: () => ({
    resumo: null,
    comparativo: null,
    loading: false,
    filtros: { data_inicio: primeiroDiaDoAno(), data_fim: '' },
  }),

  getters: {
    maiorCategoria: (state) => state.resumo?.por_categoria[0]?.categoria ?? '—',
  },

  actions: {
    // sem aviso em caso de erro: o comparativo é um complemento do Dashboard
    async fetchComparativo() {
      try {
        this.comparativo = await relatorioService.getComparativo()
      } catch {
        this.comparativo = null
      }
    },

    async fetchResumo() {
      this.loading = true
      try {
        this.resumo = await relatorioService.getResumo(this.filtros)
      } catch (error) {
        Notify.create({ type: 'negative', message: mensagemErro(error, 'Erro ao carregar relatórios.') })
      } finally {
        this.loading = false
      }
    },
  },
})

if (import.meta.hot) {
  import.meta.hot.accept(acceptHMRUpdate(useRelatoriosStore, import.meta.hot))
}
