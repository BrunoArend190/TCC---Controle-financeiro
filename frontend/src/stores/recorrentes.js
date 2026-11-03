import { defineStore, acceptHMRUpdate } from 'pinia'
import { Notify } from 'quasar'
import recorrenteService from 'src/services/recorrenteService'
import { mensagemErro } from 'boot/axios'

// o backend recebe a recorrente completa, sem os campos calculados
const paraEnvio = (r) => ({
  valor: r.valor,
  id_categoria: r.id_categoria ?? r.categoria?.id_categoria,
  estabelecimento: r.estabelecimento?.trim() || null,
  descricao: r.descricao?.trim() || null,
  dia_lancamento: Number(r.dia_lancamento),
  ativa: r.ativa,
})

export const useRecorrentesStore = defineStore('recorrentes', {
  state: () => ({
    recorrentes: [],
    loading: false,
  }),

  getters: {
    totalMensal: (state) =>
      state.recorrentes.filter((r) => r.ativa).reduce((soma, r) => soma + Number(r.valor), 0),
  },

  actions: {
    async fetchRecorrentes() {
      this.loading = true
      try {
        this.recorrentes = await recorrenteService.getAll()
      } catch (error) {
        Notify.create({ type: 'negative', message: mensagemErro(error, 'Erro ao carregar despesas recorrentes.') })
      } finally {
        this.loading = false
      }
    },

    // cria (sem id) ou edita (com id); devolve true se deu certo
    async salvarRecorrente(dados, id = null) {
      try {
        if (id) await recorrenteService.update(id, paraEnvio(dados))
        else await recorrenteService.create(paraEnvio(dados))
        Notify.create({ type: 'positive', message: `Despesa recorrente ${id ? 'atualizada' : 'criada'} com sucesso!` })
        await this.fetchRecorrentes()
        return true
      } catch (error) {
        Notify.create({ type: 'negative', message: mensagemErro(error, 'Erro ao salvar despesa recorrente.') })
        return false
      }
    },

    // pausa ou reativa os lançamentos automáticos
    async alternarAtiva(recorrente, ativa) {
      try {
        await recorrenteService.update(recorrente.id_recorrente, paraEnvio({ ...recorrente, ativa }))
        Notify.create({ type: 'positive', message: ativa ? 'Lançamentos reativados.' : 'Lançamentos pausados.' })
      } catch (error) {
        Notify.create({ type: 'negative', message: mensagemErro(error, 'Erro ao atualizar despesa recorrente.') })
      }
      await this.fetchRecorrentes()
    },

    async deleteRecorrente(id) {
      try {
        await recorrenteService.delete(id)
        this.recorrentes = this.recorrentes.filter((r) => r.id_recorrente !== id)
        Notify.create({ type: 'positive', message: 'Recorrência encerrada. As despesas já lançadas foram mantidas.' })
      } catch (error) {
        Notify.create({ type: 'negative', message: mensagemErro(error, 'Erro ao excluir despesa recorrente.') })
      }
    },
  },
})

if (import.meta.hot) {
  import.meta.hot.accept(acceptHMRUpdate(useRecorrentesStore, import.meta.hot))
}
