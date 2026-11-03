import { api } from 'boot/axios'

const endpoint = 'categorias'

export default {
  // READ (categorias padrão + personalizadas do usuário)
  async getAll() {
    const response = await api.get(endpoint)
    return response.data
  },

  // CREATE
  async create(nome) {
    const response = await api.post(endpoint, { nome })
    return response.data
  },

  // UPDATE
  async update(id, nome) {
    const response = await api.put(`${endpoint}/${id}`, { nome })
    return response.data
  },

  // DELETE
  async delete(id) {
    await api.delete(`${endpoint}/${id}`)
  },
}
