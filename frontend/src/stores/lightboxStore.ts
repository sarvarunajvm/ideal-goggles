import { create } from 'zustand';

export interface LightboxPhoto {
  id: string;
  path: string;
  thumbnail_path?: string;
  filename: string;
  metadata?: {
    width?: number;
    height?: number;
    date_taken?: string;
    camera_make?: string;
    camera_model?: string;
    iso?: number;
    aperture?: string;
    shutter_speed?: string;
    focal_length?: string;
  };
  ocr_text?: string;
  tags?: string[];
}

interface LightboxState {
  isOpen: boolean;
  currentIndex: number;
  photos: LightboxPhoto[];

  // Actions
  openLightbox: (photos: LightboxPhoto[], startIndex: number) => void;
  closeLightbox: () => void;
  nextPhoto: () => void;
  prevPhoto: () => void;
  goToPhoto: (index: number) => void;
  setPhotos: (photos: LightboxPhoto[]) => void;
}

export const useLightboxStore = create<LightboxState>((set) => ({
  isOpen: false,
  currentIndex: 0,
  photos: [],

  openLightbox: (photos, startIndex) =>
    set({
      isOpen: true,
      photos,
      currentIndex: startIndex,
    }),

  closeLightbox: () =>
    set({
      isOpen: false,
      currentIndex: 0,
    }),

  nextPhoto: () =>
    set((state) => ({
      currentIndex:
        state.currentIndex < state.photos.length - 1
          ? state.currentIndex + 1
          : state.currentIndex,
    })),

  prevPhoto: () =>
    set((state) => ({
      currentIndex: state.currentIndex > 0 ? state.currentIndex - 1 : 0,
    })),

  goToPhoto: (index) =>
    set((state) => ({
      currentIndex: Math.max(0, Math.min(index, state.photos.length - 1)),
    })),

  setPhotos: (photos) =>
    set({
      photos,
    }),
}));
