<template>
  <q-layout view="lHh Lpr lFf">
    <q-header elevated class="bg-primary" v-if="$q.screen.lt.md">
      <q-toolbar>
        <q-btn flat dense round icon="menu" aria-label="Menu" @click="drawerOpen = !drawerOpen" />
        <q-toolbar-title>Gestão Financeira</q-toolbar-title>
      </q-toolbar>
    </q-header>

    <q-drawer v-model="drawerOpen" show-if-above :width="240" :breakpoint="1023" class="bg-menu">
      <q-scroll-area class="fit">
        <div class="q-py-lg text-white text-center">
          <q-icon name="account_balance_wallet" size="48px" />
          <div class="text-h6 q-mt-xs">Gestão Financeira</div>
          <div class="text-caption text-blue-2">{{ authStore.nomeUsuario }}</div>
          <q-separator dark class="q-mt-md" />
        </div>

        <q-list padding dark>
          <EssentialLink v-for="link in essentialLinks" :key="link.title" v-bind="link" />
        </q-list>

        <q-list dark class="absolute-bottom q-mb-md">
          <q-item clickable @click="sair">
            <q-item-section avatar><q-icon name="logout" /></q-item-section>
            <q-item-section>Sair</q-item-section>
          </q-item>
        </q-list>
      </q-scroll-area>
    </q-drawer>

    <q-page-container>
      <router-view />
    </q-page-container>
  </q-layout>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from 'stores/auth'
import EssentialLink from 'components/EssentialLink.vue'

const router = useRouter()
const authStore = useAuthStore()
const drawerOpen = ref(false)

// Links do menu lateral
const essentialLinks = [
  { title: 'Dashboard', icon: 'dashboard', link: '/app', exact: true },
  { title: 'Despesas', icon: 'receipt_long', link: '/app/despesas' },
  { title: 'Enviar comprovante', icon: 'document_scanner', link: '/app/comprovante' },
  { title: 'Recorrentes', icon: 'event_repeat', link: '/app/recorrentes' },
  { title: 'Orçamentos', icon: 'savings', link: '/app/orcamentos' },
  { title: 'Categorias', icon: 'category', link: '/app/categorias' },
  { title: 'Meu perfil', icon: 'person', link: '/app/perfil' },
]

// ao recarregar a página só o token fica salvo; busca os dados do usuário
onMounted(() => {
  if (!authStore.usuario) authStore.carregarUsuario().catch(() => {})
})

function sair() {
  authStore.logout()
  router.push('/login')
}
</script>

<style lang="scss">
.bg-menu {
  background: #0b2f57 !important;
  color: white;
}

.q-drawer {
  .q-item {
    color: rgba(255, 255, 255, 0.75);
    border-left: 5px solid transparent;

    &.q-router-link--active {
      color: #fff;
      background: rgba(255, 255, 255, 0.15);
      border-left-color: #4fa3d9;
    }
  }
}
</style>
