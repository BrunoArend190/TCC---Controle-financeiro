import { defineRouter } from '#q-app/wrappers'
import {
  createRouter,
  createMemoryHistory,
  createWebHistory,
  createWebHashHistory,
} from 'vue-router'
import routes from './routes'
import { useAuthStore } from 'stores/auth'

export default defineRouter(function ({ store }) {
  const createHistory = process.env.SERVER
    ? createMemoryHistory
    : process.env.VUE_ROUTER_MODE === 'history'
      ? createWebHistory
      : createWebHashHistory

  const Router = createRouter({
    scrollBehavior: () => ({ left: 0, top: 0 }),
    routes,
    history: createHistory(process.env.VUE_ROUTER_BASE),
  })

  // Guarda de rotas: telas internas exigem login; login/cadastro não fazem sentido para quem já entrou
  Router.beforeEach((to) => {
    const auth = useAuthStore(store)
    if (to.matched.some((r) => r.meta.requerLogin) && !auth.isAutenticado) return '/login'
    if (to.meta.publica && auth.isAutenticado) return '/app'
  })

  return Router
})
