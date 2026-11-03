import { defineStore, acceptHMRUpdate } from 'pinia'
import { Notify } from 'quasar'
import despesaService from 'src/services/despesaService'
import { mensagemErro } from 'boot/axios'

export const useDespesasStore = defineStore('despesas', {
  state: () => ({
    despesas: [],
    loading: false,
    filtros: { data_inicio: '', data_fim: '', id_categoria: null, busca: '' },
  }),

  getters: {
    total: (state) => state.despesas.reduce((soma, d) => soma + Number(d.valor), 0),
  },

  actions: {
    async fetchDespesas() {
      this.loading = true
      try {
        this.despesas = await despesaService.getAll(this.filtros)
      } catch (error) {
        Notify.create({ type: 'negative', message: mensagemErro(error, 'Erro ao carregar despesas.') })
      } finally {
        this.loading = false
      }
    },

    // registro manual (sem id) ou edição (com id); devolve true se deu certo
    async salvarDespesa(dados, id = null) {
      try {
        if (id) await despesaService.update(id, dados)
        else await despesaService.create(dados)
        Notify.create({ type: 'positive', message: `Despesa ${id ? 'atualizada' : 'registrada'} com sucesso!` })
        await this.fetchDespesas()
        return true
      } catch (error) {
        Notify.create({ type: 'negative', message: mensagemErro(error, 'Erro ao salvar despesa.') })
        return false
      }
    },

    async deleteDespesa(id) {
      try {
        await despesaService.delete(id)
        this.despesas = this.despesas.filter((d) => d.id_despesa !== id)
        Notify.create({ type: 'positive', message: 'Despesa excluída com sucesso!' })
      } catch (error) {
        Notify.create({ type: 'negative', message: mensagemErro(error, 'Erro ao excluir despesa.') })
      }
    },

    // Etapa 1 do comprovante: devolve o resultado da extração (ou lança o erro)
    async extrairComprovante(arquivo) {
      try {
        return await despesaService.extrairComprovante(arquivo)
      } catch (error) {
        throw new Error(mensagemErro(error, 'Erro ao enviar o comprovante.'))
      }
    },

    // Etapa 2: confirma os dados conferidos pelo usuário
    async confirmarComprovante(dados) {
      try {
        await despesaService.confirmarComprovante(dados)
        Notify.create({ type: 'positive', message: 'Despesa registrada com o comprovante!' })
        return true
      } catch (error) {
        Notify.create({ type: 'negative', message: mensagemErro(error, 'Erro ao salvar a despesa.') })
        return false
      }
    },

    async abrirComprovante(id) {
      try {
        const arquivo = await despesaService.getComprovante(id)
        window.open(URL.createObjectURL(arquivo), '_blank')
      } catch (error) {
        Notify.create({ type: 'negative', message: mensagemErro(error, 'Comprovante indisponível.') })
      }
    },
  },
})

if (import.meta.hot) {
  import.meta.hot.accept(acceptHMRUpdate(useDespesasStore, import.meta.hot))
}
