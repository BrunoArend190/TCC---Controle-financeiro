const routes = [
  {
    path: '/',
    redirect: '/login', // ao abrir o sistema vai para o login (ou para o painel, se já logado)
  },
  {
    path: '/login',
    component: () => import('pages/LoginPage.vue'),
    meta: { publica: true },
  },
  {
    path: '/cadastro',
    component: () => import('pages/CadastroPage.vue'),
    meta: { publica: true },
  },
  {
    path: '/app',
    component: () => import('layouts/MainLayout.vue'),
    meta: { requerLogin: true },
    children: [
      { path: '', name: 'Dashboard', component: () => import('pages/IndexPage.vue') },
      { path: 'despesas', name: 'Despesas', component: () => import('pages/DespesasPage.vue') },
      { path: 'comprovante', name: 'Comprovante', component: () => import('pages/ComprovantePage.vue') },
      { path: 'recorrentes', name: 'Recorrentes', component: () => import('pages/RecorrentesPage.vue') },
      { path: 'orcamentos', name: 'Orcamentos', component: () => import('pages/OrcamentosPage.vue') },
      { path: 'categorias', name: 'Categorias', component: () => import('pages/CategoriasPage.vue') },
      { path: 'perfil', name: 'Perfil', component: () => import('pages/PerfilPage.vue') },
    ],
  },
  {
    path: '/:catchAll(.*)*',
    component: () => import('pages/ErrorNotFound.vue'),
  },
]

export default routes
