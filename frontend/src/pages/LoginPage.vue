<template>
  <div class="tela-acesso row no-wrap">
    <!-- Lado esquerdo -->
    <div class="col-6 gt-sm flex flex-center bg-primary text-white column">
      <q-icon name="account_balance_wallet" size="96px" />
      <div class="text-h5 q-mt-md">Gestão Financeira</div>
      <div class="text-subtitle1 text-blue-2 q-mt-sm text-center q-px-xl">
        Registre suas despesas enviando a foto do comprovante.
      </div>
    </div>

    <!-- Lado direito -->
    <div class="col flex flex-center">
      <q-card class="q-pa-xl shadow-2 cartao-acesso">
        <div class="text-h5 text-center q-mb-lg">Entrar</div>

        <q-form @submit.prevent="entrar">
          <q-input
            v-model="email"
            label="E-mail"
            type="email"
            outlined
            dense
            class="q-mb-md"
            :rules="[(val) => !!val || 'Informe o e-mail']"
          />
          <q-input
            v-model="senha"
            label="Senha"
            :type="mostrarSenha ? 'text' : 'password'"
            outlined
            dense
            class="q-mb-md"
            :rules="[(val) => !!val || 'Informe a senha']"
          >
            <template #append>
              <q-icon
                :name="mostrarSenha ? 'visibility_off' : 'visibility'"
                class="cursor-pointer"
                @click="mostrarSenha = !mostrarSenha"
              />
            </template>
          </q-input>

          <q-btn label="Entrar" type="submit" color="primary" class="full-width" unelevated :loading="loading" />
        </q-form>

        <div class="text-center q-mt-lg">
          Não tem conta?
          <router-link to="/cadastro" class="text-primary">Cadastre-se</router-link>
        </div>
      </q-card>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { Notify } from 'quasar'
import { useAuthStore } from 'stores/auth'
import { mensagemErro } from 'boot/axios'

defineOptions({
  name: 'LoginPage',
})

const router = useRouter()
const authStore = useAuthStore()

const email = ref('')
const senha = ref('')
const mostrarSenha = ref(false)
const loading = ref(false)

async function entrar() {
  loading.value = true
  try {
    await authStore.login(email.value, senha.value)
    router.push('/app')
  } catch (error) {
    Notify.create({ type: 'negative', message: mensagemErro(error, 'Não foi possível entrar.') })
  } finally {
    loading.value = false
  }
}
</script>

<style lang="scss" scoped>
.tela-acesso {
  min-height: 100vh;
}
.cartao-acesso {
  width: 380px;
  max-width: 92vw;
  border-radius: 12px;
}
</style>
