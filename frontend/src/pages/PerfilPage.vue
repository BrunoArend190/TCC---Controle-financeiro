<template>
  <q-page class="q-pa-none">
    <div class="header-section text-white q-pa-md q-px-lg row items-center">
      <div class="text-h5">Meu perfil</div>
    </div>

    <div class="q-pa-lg">
      <div class="row q-col-gutter-lg">
        <!-- Dados pessoais -->
        <div class="col-12 col-md-6">
          <q-card flat bordered>
            <q-card-section>
              <div class="text-subtitle1 text-weight-medium q-mb-md">Dados pessoais</div>
              <q-form @submit.prevent="salvarPerfil">
                <q-input
                  v-model="perfil.nome"
                  label="Nome"
                  maxlength="120"
                  outlined
                  dense
                  class="q-mb-sm"
                  :rules="[(val) => (val && val.trim().length >= 2) || 'Informe seu nome']"
                />
                <q-input
                  v-model="perfil.email"
                  label="E-mail"
                  type="email"
                  outlined
                  dense
                  class="q-mb-sm"
                  :rules="[(val) => !!val || 'Informe o e-mail']"
                />
                <div class="row justify-end">
                  <q-btn label="Salvar dados" color="primary" type="submit" unelevated no-caps :loading="salvandoPerfil" />
                </div>
              </q-form>
            </q-card-section>
          </q-card>
        </div>

        <!-- Senha -->
        <div class="col-12 col-md-6">
          <q-card flat bordered>
            <q-card-section>
              <div class="text-subtitle1 text-weight-medium q-mb-md">Alterar senha</div>
              <q-form ref="formSenha" @submit.prevent="salvarSenha">
                <q-input
                  v-model="senha.atual"
                  label="Senha atual"
                  type="password"
                  autocomplete="current-password"
                  outlined
                  dense
                  class="q-mb-sm"
                  :rules="[(val) => !!val || 'Informe a senha atual']"
                />
                <q-input
                  v-model="senha.nova"
                  label="Nova senha"
                  type="password"
                  autocomplete="new-password"
                  outlined
                  dense
                  class="q-mb-sm"
                  :rules="[(val) => (val && val.length >= 8) || 'A senha deve ter no mínimo 8 caracteres (RN02)']"
                />
                <q-input
                  v-model="senha.confirmacao"
                  label="Confirme a nova senha"
                  type="password"
                  autocomplete="new-password"
                  outlined
                  dense
                  class="q-mb-sm"
                  :rules="[(val) => val === senha.nova || 'As senhas não conferem']"
                />
                <div class="row justify-end">
                  <q-btn label="Alterar senha" color="primary" type="submit" unelevated no-caps :loading="salvandoSenha" />
                </div>
              </q-form>
            </q-card-section>
          </q-card>
        </div>

        <!-- Exclusão de conta -->
        <div class="col-12">
          <q-card flat bordered class="zona-perigo">
            <q-card-section class="row items-center q-col-gutter-md">
              <div class="col-12 col-sm">
                <div class="text-subtitle1 text-weight-medium text-negative">Excluir conta</div>
                <div class="text-body2 text-grey-8">
                  Apaga definitivamente sua conta, despesas, comprovantes, categorias, orçamentos e recorrências.
                  Esta ação não pode ser desfeita.
                </div>
              </div>
              <div class="col-12 col-sm-auto">
                <q-btn label="Excluir minha conta" icon="delete_forever" color="negative" outline no-caps @click="confirmarExclusao" />
              </div>
            </q-card-section>
          </q-card>
        </div>
      </div>
    </div>
  </q-page>
</template>

<script setup>
import { nextTick, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useQuasar, Notify } from 'quasar'
import { useAuthStore } from 'stores/auth'
import { mensagemErro } from 'boot/axios'

defineOptions({
  name: 'PerfilPage',
})

const $q = useQuasar()
const router = useRouter()
const authStore = useAuthStore()

const perfil = ref({ nome: '', email: '' })
const senha = ref({ atual: '', nova: '', confirmacao: '' })
const formSenha = ref(null)
const salvandoPerfil = ref(false)
const salvandoSenha = ref(false)

// o usuário pode ainda estar carregando quando a tela abre (ex.: ao recarregar a página)
watch(
  () => authStore.usuario,
  (usuario) => {
    if (usuario) perfil.value = { nome: usuario.nome, email: usuario.email }
  },
  { immediate: true },
)

async function salvarPerfil() {
  salvandoPerfil.value = true
  try {
    await authStore.atualizarPerfil({ nome: perfil.value.nome.trim(), email: perfil.value.email })
    Notify.create({ type: 'positive', message: 'Dados atualizados com sucesso!' })
  } catch (error) {
    Notify.create({ type: 'negative', message: mensagemErro(error, 'Erro ao atualizar os dados.') })
  } finally {
    salvandoPerfil.value = false
  }
}

async function salvarSenha() {
  salvandoSenha.value = true
  try {
    await authStore.alterarSenha(senha.value.atual, senha.value.nova)
    senha.value = { atual: '', nova: '', confirmacao: '' }
    await nextTick() // espera a limpeza dos campos para não exibi-los como inválidos
    formSenha.value.resetValidation()
    Notify.create({ type: 'positive', message: 'Senha alterada com sucesso!' })
  } catch (error) {
    Notify.create({ type: 'negative', message: mensagemErro(error, 'Erro ao alterar a senha.') })
  } finally {
    salvandoSenha.value = false
  }
}

// exige a senha para evitar exclusão acidental ou por outra pessoa
function confirmarExclusao() {
  $q.dialog({
    title: 'Excluir conta',
    message: 'Todos os seus dados serão apagados definitivamente. Digite sua senha para confirmar.',
    prompt: { model: '', type: 'password', label: 'Senha', outlined: true, dense: true, isValid: (val) => !!val },
    cancel: { label: 'Cancelar', flat: true },
    ok: { label: 'Excluir definitivamente', color: 'negative', unelevated: true },
    persistent: true,
  }).onOk(async (senhaDigitada) => {
    try {
      await authStore.excluirConta(senhaDigitada)
      Notify.create({ type: 'positive', message: 'Sua conta foi excluída.' })
      router.push('/login')
    } catch (error) {
      Notify.create({ type: 'negative', message: mensagemErro(error, 'Erro ao excluir a conta.') })
    }
  })
}
</script>

<style lang="scss" scoped>
.zona-perigo {
  border-color: $negative;
}
</style>
