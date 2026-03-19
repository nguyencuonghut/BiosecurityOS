import { createApp } from 'vue'
import { createPinia } from 'pinia'
import PrimeVue from 'primevue/config'
import Aura from '@primeuix/themes/aura'
import { definePreset } from '@primeuix/themes'
import ToastService from 'primevue/toastservice'
import ConfirmationService from 'primevue/confirmationservice'
import Tooltip from 'primevue/tooltip'
import 'primeicons/primeicons.css'
import '@/styles/mobile.css'

import App from './App.vue'
import router from './router/index.js'

const BiosecurityPreset = definePreset(Aura, {
  components: {
    tag: {
      colorScheme: {
        dark: {
          primary: { background: '{primary.500}', color: '{surface.0}' },
          secondary: { background: '{surface.600}', color: '{surface.0}' },
          success: { background: '{green.500}', color: '{surface.0}' },
          info: { background: '{sky.500}', color: '{surface.0}' },
          warn: { background: '{orange.500}', color: '{surface.0}' },
          danger: { background: '{red.500}', color: '{surface.0}' },
        },
      },
    },
  },
})

const app = createApp(App)

app.use(createPinia())
app.use(router)
app.use(PrimeVue, {
  theme: {
    preset: BiosecurityPreset,
    options: {
      darkModeSelector: '.app-dark',
    },
  },
})
app.use(ToastService)
app.use(ConfirmationService)
app.directive('tooltip', Tooltip)

app.mount('#app')
