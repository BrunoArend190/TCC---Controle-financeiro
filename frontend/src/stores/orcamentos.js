import { defineStore, acceptHMRUpdate } from 'pinia'
import { Notify } from 'quasar'
import orcamentoService from 'src/services/orcamentoService'
import { mensagemErro } from 'boot/axios'
import { hojeISO } from 'src/utils/formatadores'

export const useOrcamentosStore = defineStore('orcamentos', {
  state: () => ({
    orcamentos: [],
    loading: false,
    mes: hojeISO().slice(0, 7), // AAAA-MM
  }),

  getters: {
    // orçamentos em alerta ou estourados (exibidos no Dashboard)
    emAtencao: (state) => state.orcamentos.filter((o) => o.situacao !== 'ok'),
    totalLimite: (state) => state.orcamentos.reduce((soma, o) => soma + Number(o.valor_limite), 0),
    totalGasto: (state) => state.orcamentos.reduce((soma, o) => soma + Number(o.gasto), 0),
  },

  actions: {
    async fetchOrcamentos() {
      this.loading = true
      try {
        this.orcamentos = await orcamentoService.getAll(this.mes)
      } catch (error) {
        Notify.create({ type: 'negative', message: mensagemErro(error, 'Erro ao carregar orçamentos.') })
      } finally {
        this.loading = false
      }
    },

    // cria ou altera o limite; devolve true se deu certo
    async salvarOrcamento(idCategoria, valorLimite) {
      try {
        await orcamentoService.definir(idCategoria, valorLimite)
        Notify.create({ type: 'positive', message: 'Orçamento salvo com sucesso!' })
        await this.fetchOrcamentos()
        return true
      } catch (error) {
        Notify.create({ type: 'negative', message: mensagemErro(error, 'Erro ao salvar orçamento.') })
        return false
      }
    },

    async deleteOrcamento(idCategoria) {
      try {
        await orcamentoService.delete(idCategoria)
        this.orcamentos = this.orcamentos.filter((o) => o.categoria.id_categoria !== idCategoria)
        Notify.create({ type: 'positive', message: 'Orçamento removido.' })
      } catch (error) {
        Notify.create({ type: 'negative', message: mensagemErro(error, 'Erro ao remover orçamento.') })
      }
    },
  },
})

if (import.meta.hot) {
  import.meta.hot.accept(acceptHMRUpdate(useOrcamentosStore, import.meta.hot))
}
