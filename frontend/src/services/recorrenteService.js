import { api } from 'boot/axios'

const endpoint = 'recorrentes'

export default {
  // READ
  async getAll() {
    const response = await api.get(endpoint)
    return response.data
  },

  // CREATE
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
}
