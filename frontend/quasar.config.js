// Configuração do Quasar (https://v2.quasar.dev/quasar-cli-vite/quasar-config-file)
import { defineConfig } from '#q-app/wrappers'

export default defineConfig(() => {
  return {
    // arquivos executados antes da aplicação subir (src/boot)
    boot: ['axios'],

    css: ['app.scss'],

    extras: ['roboto-font', 'material-icons'],

    build: {
      target: {
        browser: ['es2022', 'firefox115', 'chrome115', 'safari14'],
        node: 'node20',
      },
      vueRouterMode: 'hash',
      vitePlugins: [
        [
          'vite-plugin-checker',
          {
            eslint: {
              lintCommand: 'eslint -c ./eslint.config.js "./src*/**/*.{js,mjs,cjs,vue}"',
              useFlatConfig: true,
            },
          },
          { server: false },
        ],
      ],
    },

    devServer: {
      port: 5173,
      allowedHosts: ['.trycloudflare.com'], // libera o link público do túnel (iniciar.bat)
      // Sem atualização automática (HMR) quando iniciado pelo iniciar.bat: pelo túnel, a conexão do HMR cai
      // (ex.: celular abre a câmera) e o Vite recarrega a página, cancelando a extração em andamento.
      ws: process.env.SEM_HMR ? false : undefined,
      open: !process.env.SEM_NAVEGADOR, // abre o navegador automaticamente ao rodar "npm run dev"
      // as chamadas a /api são repassadas para o backend FastAPI (evita CORS)
      proxy: {
        '/api': {
          target: 'http://localhost:8000',
          changeOrigin: true,
          rewrite: (path) => path.replace(/^\/api/, ''),
        },
      },
    },

    framework: {
      lang: 'pt-BR',
      config: {
        notify: { position: 'top-right', timeout: 2500 },
      },
      plugins: ['Notify', 'Dialog'],
    },

    animations: [],
  }
})
