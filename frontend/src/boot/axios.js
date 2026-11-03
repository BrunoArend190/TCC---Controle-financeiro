import { defineBoot } from '#q-app/wrappers'
import axios from 'axios'
import { useAuthStore } from 'stores/auth'

// Instância do Axios apontando para o backend FastAPI.
// Em desenvolvimento, "/api" é repassado para http://localhost:8000 (proxy do quasar.config.js).
const api = axios.create({ baseURL: '/api' })

export const CHAVE_TOKEN = 'token'

// Envia o token JWT em todas as requisições
api.interceptors.request.use((config) => {
  const token = localStorage.getItem(CHAVE_TOKEN)
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

// Converte a resposta de erro da API em uma mensagem legível
export function mensagemErro(error, padrao = 'Erro inesperado') {
  const detalhe = error?.response?.data?.detail
  if (typeof detalhe === 'string') return detalhe
  if (Array.isArray(detalhe)) return detalhe.map((d) => d.msg.replace(/^Value error, /, '')).join('; ')
  if (!error?.response) return 'Não foi possível conectar ao servidor'
  return padrao
}

export default defineBoot(({ app, router, store }) => {
  // Sessão expirada: encerra a sessão na store e volta para o login
  api.interceptors.response.use(
    (response) => response,
    (error) => {
      const url = error.config?.url || ''
      if (error.response?.status === 401 && !url.includes('auth/login')) {
        useAuthStore(store).logout()
        router.push('/login')
      }
      return Promise.reject(error)
    },
  )

  // permite usar this.$axios e this.$api nos componentes (Options API)
  app.config.globalProperties.$axios = axios
  app.config.globalProperties.$api = api
})

export { api }
