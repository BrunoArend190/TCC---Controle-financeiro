import { defineStore, acceptHMRUpdate, getActivePinia } from 'pinia'
import authService from 'src/services/authService'
import { CHAVE_TOKEN } from 'boot/axios'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    token: localStorage.getItem(CHAVE_TOKEN),
    usuario: null,
  }),

  getters: {
    isAutenticado: (state) => !!state.token,
    nomeUsuario: (state) => state.usuario?.nome ?? '',
  },

  actions: {
    async login(email, senha) {
      const { access_token } = await authService.login(email, senha)
      this.token = access_token
      localStorage.setItem(CHAVE_TOKEN, access_token)
      await this.carregarUsuario()
    },

    async cadastrar(dados) {
      await authService.cadastrar(dados)
      await this.login(dados.email, dados.senha)
    },

    async carregarUsuario() {
      this.usuario = await authService.me()
    },

    async atualizarPerfil(dados) {
      this.usuario = await authService.atualizarPerfil(dados)
    },

    async alterarSenha(senhaAtual, novaSenha) {
      await authService.alterarSenha(senhaAtual, novaSenha)
    },

    async excluirConta(senha) {
      await authService.excluirConta(senha)
      this.logout()
    },

    logout() {
      this.token = null
      this.usuario = null
      localStorage.removeItem(CHAVE_TOKEN)
      // limpa as demais stores para o próximo usuário não ver dados desta sessão
      getActivePinia()._s.forEach((store) => {
        if (store.$id !== 'auth') store.$reset()
      })
    },
  },
})

if (import.meta.hot) {
  import.meta.hot.accept(acceptHMRUpdate(useAuthStore, import.meta.hot))
}
