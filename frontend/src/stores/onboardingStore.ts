import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface OnboardingState {
  completed: boolean;
  currentStep: number;
  selectedFolders: string[];
  indexingStarted: boolean;
  skipOnboarding: boolean;

  // Actions
  setCompleted: () => void;
  nextStep: () => void;
  prevStep: () => void;
  setCurrentStep: (step: number) => void;
  addFolder: (path: string) => void;
  removeFolder: (path: string) => void;
  setIndexingStarted: (started: boolean) => void;
  setSkipOnboarding: (skip: boolean) => void;
  reset: () => void;
}

const initialState = {
  completed: false,
  currentStep: 0,
  selectedFolders: [],
  indexingStarted: false,
  skipOnboarding: false,
};

export const useOnboardingStore = create<OnboardingState>()(
  persist(
    (set) => ({
      ...initialState,

      setCompleted: () => set({ completed: true }),

      nextStep: () =>
        set((state) => ({ currentStep: state.currentStep + 1 })),

      prevStep: () =>
        set((state) => ({
          currentStep: Math.max(0, state.currentStep - 1),
        })),

      setCurrentStep: (step: number) => set({ currentStep: step }),

      addFolder: (path: string) =>
        set((state) => ({
          selectedFolders: [...state.selectedFolders, path],
        })),

      removeFolder: (path: string) =>
        set((state) => ({
          selectedFolders: state.selectedFolders.filter((f) => f !== path),
        })),

      setIndexingStarted: (started: boolean) =>
        set({ indexingStarted: started }),

      setSkipOnboarding: (skip: boolean) => set({ skipOnboarding: skip }),

      reset: () => set(initialState),
    }),
    {
      name: 'onboarding-storage',
      version: 1,
    }
  )
);
