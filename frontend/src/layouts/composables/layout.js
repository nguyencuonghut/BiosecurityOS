import { computed, reactive } from 'vue'

const savedDark = localStorage.getItem('biosecurity-dark-mode') === 'true'

const layoutState = reactive({
  sidebarVisible: true,
  mobileMenuActive: false,
  staticMenuInactive: false,
  darkMode: savedDark,
})

// Apply on initial load
if (savedDark) {
  document.documentElement.classList.add('app-dark')
}

export function useLayout() {
  const toggleSidebar = () => {
    if (isDesktop()) {
      layoutState.staticMenuInactive = !layoutState.staticMenuInactive
    } else {
      layoutState.mobileMenuActive = !layoutState.mobileMenuActive
    }
  }

  const hideMobileMenu = () => {
    layoutState.mobileMenuActive = false
  }

  const toggleDarkMode = () => {
    layoutState.darkMode = !layoutState.darkMode
    if (layoutState.darkMode) {
      document.documentElement.classList.add('app-dark')
    } else {
      document.documentElement.classList.remove('app-dark')
    }
    localStorage.setItem('biosecurity-dark-mode', layoutState.darkMode)
  }

  const isDesktop = () => window.innerWidth > 991

  const containerClass = computed(() => ({
    'layout-static-inactive': layoutState.staticMenuInactive && isDesktop(),
    'layout-mobile-active': layoutState.mobileMenuActive && !isDesktop(),
    'app-dark': layoutState.darkMode,
  }))

  return {
    layoutState,
    toggleSidebar,
    hideMobileMenu,
    toggleDarkMode,
    isDesktop,
    containerClass,
  }
}
