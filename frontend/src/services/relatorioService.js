import { api } from 'boot/axios'

export default {
  // Total gasto, quantidade e totais por categoria e por mês
  async getResumo(filtros = {}) {
    const params = Object.fromEntries(Object.entries(filtros).filter(([, v]) => v))
    const response = await api.get('relatorios/resumo', { params })
    return response.data
  },

  // Frases comparando o mês atual com o mesmo período do mês anterior
  async getComparativo() {
    const response = await api.get('relatorios/comparativo')
    return response.data
  },
}
