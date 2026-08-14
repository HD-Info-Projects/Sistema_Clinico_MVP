// https://nuxt.com/docs/api/configuration/nuxt-config
const DEFAULT_AUTH_MAX_AGE_SECONDS = 60 * 60 * 24 * 7
const authCookieMaxAgeSeconds = Number(process.env.NUXT_PUBLIC_AUTH_COOKIE_MAX_AGE_SECONDS || DEFAULT_AUTH_MAX_AGE_SECONDS)

export default defineNuxtConfig({

  modules: [
    '@nuxt/eslint',
    '@nuxt/ui',
    '@nuxt/image',
    '@pinia/nuxt',
    '@vueuse/nuxt'
  ],

  devtools: {
    enabled: true
  },

  css: ['~/assets/css/main.css'],
  colorMode: {
    preference: 'light'
  },

  ui: {
    theme: {
      colors: ['tertiary', 'error', 'success', 'info', 'warning', 'secondary', 'quaternary', 'quinary']
    }
  },
  runtimeConfig: {
    flaskBaseUrl: process.env.NUXT_FLASK_BASE_URL || 'http://localhost:5000',
    enableTts: process.env.NUXT_ENABLE_TTS === 'true',
    public: {
      authCookieMaxAgeSeconds: Number.isFinite(authCookieMaxAgeSeconds)
        ? authCookieMaxAgeSeconds
        : DEFAULT_AUTH_MAX_AGE_SECONDS
    }
  },

  routeRules: {
    '/': { prerender: true }
  },

  compatibilityDate: '2025-01-15',

  vite: {
    optimizeDeps: {
      include: [
        '@nuxt/ui > prosemirror-state',
        '@nuxt/ui > prosemirror-transform',
        '@nuxt/ui > prosemirror-model',
        '@nuxt/ui > prosemirror-view',
        '@nuxt/ui > prosemirror-gapcursor'
      ]
    }
  },

  eslint: {
    config: {
      stylistic: {
        commaDangle: 'never',
        braceStyle: '1tbs'
      }
    }
  }
})
