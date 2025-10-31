// https://nuxt.com/docs/api/configuration/nuxt-config
export default defineNuxtConfig({
  compatibilityDate: '2025-07-15',
  pages: true,
  devtools: { enabled: true },

  // <head> 설정 
  app: {
    head: {
      // Google Fonts: Inter and JetBrains Mono
      link: [
        {
          rel: 'preconnect',
          href: 'https://fonts.googleapis.com'
        },
        {
          rel: 'preconnect',
          href: 'https://fonts.gstatic.com',
          crossorigin: ''
        },
        {
          rel: 'stylesheet',
          href: 'https://fonts.googleapis.com/css2?family=Inter:wght@400;700&family=JetBrains+Mono&display=swap'
        }
      ]
    }
  },

  // Server Side Rendering 활성화
  ssr: true,

  plugins: ["~/plugins/vuetify"],
  modules: ["@pinia/nuxt"],

  // 📌 Runtime Config (환경 변수)
  runtimeConfig: {
    // 클라이언트에 공개되지 않는 환경변수 정의
    // apiSecret: process.env.API_SECRET,

    // client에 공개하는 환경변수는 NUXT_PUBLIC_ 접두사 필수
    public: {
      defaultPage: process.env.NUXT_PUBLIC_DEFAULT_ACCESS_PAGE || "home",
      baseUrl: process.env.NUXT_PUBLIC_BASE_URL || "http://20.33.67.16:8000"
    },
  },

  // 📌 Global CSS 설정
  css: [
    "@/assets/scss/main.scss", // ** Newly Added Global Styles **
    "vuetify/lib/styles/main.css", // Vuetify 
    "@mdi/font/css/materialdesignicons.css", // MDI 아이콘
    "@/assets/scss/font.scss",
    "@/assets/scss/color.scss",
    "@/assets/scss/size.scss"
  ],

  // 📌 Vite 설정 (필요하면 추가)
  vite: {
    define: {
      "process.env.DEBUG": false // 디버깅 로그 출력으로 성능저하 가능성 있으므로 비활성화
    }
  },

  build: {
    transpile: ["vuetify"] // Vuetify 트랜스파일링 추가
  },
})
