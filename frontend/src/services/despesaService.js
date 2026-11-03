import { api } from 'boot/axios'

const endpoint = 'despesas'

// remove filtros vazios antes de enviar na URL
const limpar = (filtros = {}) => Object.fromEntries(Object.entries(filtros).filter(([, v]) => v))

export default {
  // READ (com filtros de período, categoria e busca)
  async getAll(filtros) {
    const response = await api.get(endpoint, { params: limpar(filtros) })
    return response.data
  },

  // CREATE (registro manual)
  async create(dados) {
    const response = await api.post(endpoint, dados)
    return response.data
  },

  // UPDATE
  async update(id, dados) {
    const response = await api.put(`${endpoint}/${id}`, dados)
    return response.data
  },

  // DELETE
  async delete(id) {
    await api.delete(`${endpoint}/${id}`)
  },

  // Etapa 1 do registro por comprovante: envia o arquivo para o NuExtract3
  async extrairComprovante(arquivo) {
    const form = new FormData()
    form.append('arquivo', arquivo)
    const response = await api.post(`${endpoint}/comprovante/extrair`, form, { timeout: 300000 })
    return response.data
  },

  // Etapa 2: grava a despesa com os dados conferidos pelo usuário
  async confirmarComprovante(dados) {
    const response = await api.post(`${endpoint}/comprovante/confirmar`, dados)
    return response.data
  },

  // Arquivo do comprovante anexado
  async getComprovante(id) {
    const response = await api.get(`${endpoint}/${id}/comprovante`, { responseType: 'blob' })
    return response.data
  },
}
