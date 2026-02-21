export default defineNuxtConfig({
  srcDir: "app",
  modules: [
    "@nuxt/ui",
    "@pinia/nuxt",
    "@pinia-plugin-persistedstate/nuxt",
    "@vueuse/nuxt",
  ],
  runtimeConfig: {
    public: {
      apiBase: process.env.NUXT_PUBLIC_API_BASE || "http://localhost/api",
    },
  },
  ssr: true,
  devtools: { enabled: true },
})
