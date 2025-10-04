import { create } from 'zustand';

export interface BatchSelection {
  selectedIds: Set<string>;
  selectionMode: boolean;
}

interface BatchSelectionState {
  selectedIds: Set<string>;
  selectionMode: boolean;

  // Actions
  toggleSelectionMode: () => void;
  enableSelectionMode: () => void;
  disableSelectionMode: () => void;
  toggleSelection: (id: string) => void;
  selectAll: (ids: string[]) => void;
  clearSelection: () => void;
  isSelected: (id: string) => boolean;
  getSelectedCount: () => number;
  getSelectedIds: () => string[];
}

export const useBatchSelectionStore = create<BatchSelectionState>((set, get) => ({
  selectedIds: new Set(),
  selectionMode: false,

  toggleSelectionMode: () =>
    set((state) => ({
      selectionMode: !state.selectionMode,
      selectedIds: !state.selectionMode ? state.selectedIds : new Set(),
    })),

  enableSelectionMode: () =>
    set({
      selectionMode: true,
    }),

  disableSelectionMode: () =>
    set({
      selectionMode: false,
      selectedIds: new Set(),
    }),

  toggleSelection: (id: string) =>
    set((state) => {
      const newSelectedIds = new Set(state.selectedIds);
      if (newSelectedIds.has(id)) {
        newSelectedIds.delete(id);
      } else {
        newSelectedIds.add(id);
      }
      return { selectedIds: newSelectedIds };
    }),

  selectAll: (ids: string[]) =>
    set({
      selectedIds: new Set(ids),
      selectionMode: true,
    }),

  clearSelection: () =>
    set({
      selectedIds: new Set(),
    }),

  isSelected: (id: string) => get().selectedIds.has(id),

  getSelectedCount: () => get().selectedIds.size,

  getSelectedIds: () => Array.from(get().selectedIds),
}));
