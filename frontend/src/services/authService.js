import { api } from 'boot/axios'

export default {
  // CREATE (cadastro de usuário)
  async cadastrar(dados) {
    const response = await api.post('auth/cadastro', dados)
    return response.data
  },

  // Login: a API espera um formulário (OAuth2) com username = e-mail
  async login(email, senha) {
    const form = new URLSearchParams({ username: email, password: senha })
    const response = await api.post('auth/login', form)
    return response.data
  },

  // READ (usuário logado)
  async me() {
    const response = await api.get('auth/me')
    return response.data
  },

  // UPDATE (nome e e-mail)
  async atualizarPerfil(dados) {
    const response = await api.put('auth/me', dados)
    return response.data
  },

  async alterarSenha(senhaAtual, novaSenha) {
    await api.put('auth/me/senha', { senha_atual: senhaAtual, nova_senha: novaSenha })
  },

  // DELETE (a senha é confirmada no corpo da requisição)
  async excluirConta(senha) {
    await api.post('auth/me/excluir', { senha })
  },
}
