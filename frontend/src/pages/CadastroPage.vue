<template>
  <div class="tela-acesso row no-wrap">
    <!-- Lado esquerdo -->
    <div class="col-6 gt-sm flex flex-center bg-primary text-white column">
      <q-icon name="account_balance_wallet" size="96px" />
      <div class="text-h5 q-mt-md">Gestão Financeira</div>
      <div class="text-subtitle1 text-blue-2 q-mt-sm text-center q-px-xl">
        Crie sua conta para começar a controlar seus gastos.
      </div>
    </div>

    <!-- Lado direito -->
    <div class="col flex flex-center">
      <q-card class="q-pa-xl shadow-2 cartao-acesso">
        <div class="text-h5 text-center q-mb-lg">Criar conta</div>

        <q-form @submit.prevent="cadastrar">
          <q-input
            v-model="dados.nome"
            label="Nome"
            outlined
            dense
            class="q-mb-sm"
            :rules="[(val) => (val && val.trim().length >= 2) || 'Informe seu nome']"
          />
          <q-input
            v-model="dados.email"
            label="E-mail"
            type="email"
            outlined
            dense
            class="q-mb-sm"
            :rules="[(val) => !!val || 'Informe o e-mail']"
          />
          <q-input
            v-model="dados.senha"
            label="Senha"
            type="password"
            outlined
            dense
            class="q-mb-sm"
            hint="Mínimo de 8 caracteres"
            :rules="[(val) => (val && val.length >= 8) || 'A senha deve ter no mínimo 8 caracteres (RN02)']"
          />
          <q-input
            v-model="confirmacao"
            label="Confirme a senha"
            type="password"
            outlined
            dense
            class="q-mb-md"
            :rules="[(val) => val === dados.senha || 'As senhas não conferem']"
          />

          <q-btn label="Cadastrar" type="submit" color="primary" class="full-width" unelevated :loading="loading" />
        </q-form>

        <div class="text-center q-mt-lg">
          Já tem conta?
          <router-link to="/login" class="text-primary">Entrar</router-link>
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
  name: 'CadastroPage',
})

const router = useRouter()
const authStore = useAuthStore()

const dados = ref({ nome: '', email: '', senha: '' })
const confirmacao = ref('')
const loading = ref(false)

async function cadastrar() {
  loading.value = true
  try {
    await authStore.cadastrar({ ...dados.value, nome: dados.value.nome.trim() })
    Notify.create({ type: 'positive', message: 'Conta criada com sucesso!' })
    router.push('/app')
  } catch (error) {
    Notify.create({ type: 'negative', message: mensagemErro(error, 'Não foi possível criar a conta.') })
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
