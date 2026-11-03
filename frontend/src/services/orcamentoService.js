import { api } from 'boot/axios'

const endpoint = 'orcamentos'

export default {
  // READ (orçamentos com o gasto do mês; mes no formato AAAA-MM)
  async getAll(mes) {
    const response = await api.get(endpoint, { params: mes ? { mes } : {} })
    return response.data
  },

  // CREATE / UPDATE: cada categoria tem no máximo um orçamento
  async definir(idCategoria, valorLimite) {
    await api.put(`${endpoint}/${idCategoria}`, { valor_limite: valorLimite })
  },

  // DELETE
  async delete(idCategoria) {
    await api.delete(`${endpoint}/${idCategoria}`)
  },
}
