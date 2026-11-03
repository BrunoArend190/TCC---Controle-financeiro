import { defineStore, acceptHMRUpdate } from 'pinia'
import { Notify } from 'quasar'
import categoriaService from 'src/services/categoriaService'
import { mensagemErro } from 'boot/axios'

export const useCategoriasStore = defineStore('categorias', {
  state: () => ({
    categorias: [],
    loading: false,
  }),

  getters: {
    // opções no formato do q-select
    opcoes: (state) => state.categorias.map((c) => ({ label: c.nome, value: c.id_categoria })),
  },

  actions: {
    async fetchCategorias() {
      this.loading = true
      try {
        this.categorias = await categoriaService.getAll()
      } catch (error) {
        Notify.create({ type: 'negative', message: mensagemErro(error, 'Erro ao carregar categorias.') })
      } finally {
        this.loading = false
      }
    },

    // cria ou renomeia; devolve true se deu certo
    async salvarCategoria({ id, nome }) {
      try {
        if (id) await categoriaService.update(id, nome)
        else await categoriaService.create(nome)
        Notify.create({ type: 'positive', message: `Categoria ${id ? 'renomeada' : 'criada'} com sucesso!` })
        await this.fetchCategorias()
        return true
      } catch (error) {
        Notify.create({ type: 'negative', message: mensagemErro(error, 'Erro ao salvar categoria.') })
        return false
      }
    },

    async deleteCategoria(id) {
      try {
        await categoriaService.delete(id)
        this.categorias = this.categorias.filter((c) => c.id_categoria !== id)
        Notify.create({ type: 'positive', message: 'Categoria removida. Suas despesas foram para "Não categorizado".' })
      } catch (error) {
        Notify.create({ type: 'negative', message: mensagemErro(error, 'Erro ao remover categoria.') })
      }
    },
  },
})

if (import.meta.hot) {
  import.meta.hot.accept(acceptHMRUpdate(useCategoriasStore, import.meta.hot))
}
