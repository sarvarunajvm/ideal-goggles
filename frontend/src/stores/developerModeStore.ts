import { create } from 'zustand'

interface DeveloperModeState {
  isDeveloperMode: boolean
  setDeveloperMode: (enabled: boolean) => void
}

export const useDeveloperModeStore = create<DeveloperModeState>((set) => ({
  isDeveloperMode: false,
  setDeveloperMode: (enabled: boolean) => set({ isDeveloperMode: enabled }),
}))