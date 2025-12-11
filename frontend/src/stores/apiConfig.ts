import { defineStore } from 'pinia'
import type { Config } from '../api'

type ProviderConfig = Record<string, any>

interface ConfigBlock {
  active_provider: string
  providers: Record<string, ProviderConfig>
}

interface ApiConfigState {
  textConfig: ConfigBlock
  imageConfig: ConfigBlock
  initialized: boolean
  lastSavedAt: number | null
  saveMessage: string
}

const OUTLINE_STORAGE_KEY = 'redink_outline_config'
const IMAGE_STORAGE_KEY = 'redink_image_config'

const createDefaultBlock = (): ConfigBlock => ({
  active_provider: '',
  providers: {}
})

function maskApiKey(key?: string): string {
  if (!key) return ''
  if (key.length <= 8) {
    return '*'.repeat(key.length)
  }
  return `${key.slice(0, 4)}${'*'.repeat(key.length - 8)}${key.slice(-4)}`
}

function readConfigFromStorage(key: string): ConfigBlock | null {
  if (typeof window === 'undefined') return null
  try {
    const raw = window.localStorage.getItem(key)
    if (!raw) return null
    const parsed = JSON.parse(raw)
    if (parsed && typeof parsed === 'object') {
      return {
        active_provider: parsed.active_provider || '',
        providers: parsed.providers || {}
      }
    }
  } catch (error) {
    console.error('加载本地配置失败:', error)
  }
  return null
}

function writeConfigToStorage(key: string, block: ConfigBlock) {
  if (typeof window === 'undefined') return
  try {
    window.localStorage.setItem(key, JSON.stringify(block))
  } catch (error) {
    console.error('保存配置失败:', error)
  }
}

function mergeProvider(existing: ProviderConfig | undefined, incoming: ProviderConfig): ProviderConfig {
  const merged: ProviderConfig = existing ? { ...existing } : {}

  for (const [key, value] of Object.entries(incoming)) {
    if (value === undefined) continue
    merged[key] = value
  }

  if (merged.api_key) {
    merged.api_key_masked = maskApiKey(String(merged.api_key))
  } else if ('api_key_masked' in incoming) {
    merged.api_key_masked = incoming.api_key_masked
  } else if (existing?.api_key_masked) {
    merged.api_key_masked = existing.api_key_masked
  } else {
    merged.api_key_masked = ''
  }

  if (!merged.api_key) {
    merged.api_key = ''
  }

  return merged
}

function sanitizeServerProvider(provider: ProviderConfig): ProviderConfig {
  const next = { ...provider }
  if (next.api_key === '' || next.api_key === undefined) {
    delete next.api_key
  }
  return next
}

function mergeConfigBlock(
  serverBlock: ConfigBlock | undefined,
  localBlock: ConfigBlock
): ConfigBlock {
  if (!serverBlock) {
    return {
      active_provider: localBlock.active_provider,
      providers: { ...localBlock.providers }
    }
  }

  const mergedProviders: Record<string, ProviderConfig> = {}

  const serverProviders = serverBlock.providers || {}
  const localProviders = localBlock.providers || {}

  for (const [name, provider] of Object.entries(serverProviders)) {
    mergedProviders[name] = mergeProvider(localProviders[name], sanitizeServerProvider(provider))
  }

  for (const [name, provider] of Object.entries(localProviders)) {
    if (!mergedProviders[name]) {
      mergedProviders[name] = mergeProvider(undefined, provider)
    }
  }

  return {
    active_provider: serverBlock.active_provider || localBlock.active_provider,
    providers: mergedProviders
  }
}

function clearProviderSecrets(providers: Record<string, ProviderConfig>): Record<string, ProviderConfig> {
  const cleared: Record<string, ProviderConfig> = {}
  Object.entries(providers || {}).forEach(([name, provider]) => {
    const next = { ...provider }
    next.api_key = ''
    next.api_key_masked = ''
    cleared[name] = next
  })
  return cleared
}

export const useApiConfigStore = defineStore('apiConfig', {
  state: (): ApiConfigState => ({
    textConfig: createDefaultBlock(),
    imageConfig: createDefaultBlock(),
    initialized: false,
    lastSavedAt: null,
    saveMessage: ''
  }),
  actions: {
    init() {
      if (this.initialized) return
      const storedText = readConfigFromStorage(OUTLINE_STORAGE_KEY)
      const storedImage = readConfigFromStorage(IMAGE_STORAGE_KEY)

      if (storedText) {
        this.textConfig = storedText
      }
      if (storedImage) {
        this.imageConfig = storedImage
      }

      if (
        (storedText && Object.keys(storedText.providers || {}).length > 0) ||
        (storedImage && Object.keys(storedImage.providers || {}).length > 0)
      ) {
        this.saveMessage = '已从本地缓存加载'
        this.lastSavedAt = Date.now()
      }

      this.initialized = true
    },

    applyServerConfig(config: Config, options?: { silent?: boolean; message?: string }) {
      this.init()
      this.textConfig = mergeConfigBlock(config?.text_generation, this.textConfig)
      this.imageConfig = mergeConfigBlock(config?.image_generation, this.imageConfig)
      this.persistAll(options?.message || '配置已同步', options?.silent === true)
    },

    setTextProvider(name: string, providerData: ProviderConfig) {
      this.init()
      const next = mergeProvider(this.textConfig.providers[name], providerData)
      this.textConfig = {
        ...this.textConfig,
        providers: {
          ...this.textConfig.providers,
          [name]: next
        }
      }
      if (!this.textConfig.active_provider) {
        this.textConfig.active_provider = name
      }
      this.persistTextConfig()
    },

    removeTextProvider(name: string) {
      this.init()
      const providers = { ...this.textConfig.providers }
      delete providers[name]
      this.textConfig = {
        ...this.textConfig,
        providers
      }
      if (this.textConfig.active_provider === name) {
        this.textConfig.active_provider = Object.keys(providers)[0] || ''
      }
      this.persistTextConfig()
    },

    setActiveTextProvider(name: string) {
      this.init()
      this.textConfig.active_provider = name
      this.persistTextConfig()
    },

    setImageProvider(name: string, providerData: ProviderConfig) {
      this.init()
      const next = mergeProvider(this.imageConfig.providers[name], providerData)
      this.imageConfig = {
        ...this.imageConfig,
        providers: {
          ...this.imageConfig.providers,
          [name]: next
        }
      }
      if (!this.imageConfig.active_provider) {
        this.imageConfig.active_provider = name
      }
      this.persistImageConfig()
    },

    removeImageProvider(name: string) {
      this.init()
      const providers = { ...this.imageConfig.providers }
      delete providers[name]
      this.imageConfig = {
        ...this.imageConfig,
        providers
      }
      if (this.imageConfig.active_provider === name) {
        this.imageConfig.active_provider = Object.keys(providers)[0] || ''
      }
      this.persistImageConfig()
    },

    setActiveImageProvider(name: string) {
      this.init()
      this.imageConfig.active_provider = name
      this.persistImageConfig()
    },

    clearLocalCache() {
      this.init()
      if (typeof window !== 'undefined') {
        window.localStorage.removeItem(OUTLINE_STORAGE_KEY)
        window.localStorage.removeItem(IMAGE_STORAGE_KEY)
      }
      this.textConfig = {
        ...this.textConfig,
        providers: clearProviderSecrets(this.textConfig.providers)
      }
      this.imageConfig = {
        ...this.imageConfig,
        providers: clearProviderSecrets(this.imageConfig.providers)
      }
      this.saveMessage = '本地缓存已清除'
      this.lastSavedAt = Date.now()
    },

    persistTextConfig(message?: string, silent?: boolean) {
      this.init()
      writeConfigToStorage(OUTLINE_STORAGE_KEY, this.textConfig)
      if (!silent) {
        this.markSaved(message)
      }
    },

    persistImageConfig(message?: string, silent?: boolean) {
      this.init()
      writeConfigToStorage(IMAGE_STORAGE_KEY, this.imageConfig)
      if (!silent) {
        this.markSaved(message)
      }
    },

    persistAll(message?: string, silent?: boolean) {
      this.init()
      writeConfigToStorage(OUTLINE_STORAGE_KEY, this.textConfig)
      writeConfigToStorage(IMAGE_STORAGE_KEY, this.imageConfig)
      if (!silent) {
        this.markSaved(message)
      }
    },

    markSaved(message?: string) {
      this.saveMessage = message || '配置已自动保存'
      this.lastSavedAt = Date.now()
    }
  }
})

export function setupApiConfigStore() {
  if (typeof window === 'undefined') return
  const store = useApiConfigStore()
  store.init()
}
