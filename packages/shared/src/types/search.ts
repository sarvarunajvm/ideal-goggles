/**
 * Search-related types and enums
 */

import type { SearchResultItem } from './api'

export type SearchMode = 'text' | 'semantic' | 'image' | 'face'

export type MatchType = 'filename' | 'folder' | 'ocr' | 'exif' | 'face' | 'image'

export type IndexingPhase = 'discovery' | 'metadata' | 'ocr' | 'embeddings' | 'faces'

export type IndexingStatus = 'idle' | 'indexing' | 'error'

export interface SearchFilter {
  dateFrom?: Date
  dateTo?: Date
  folder?: string
  hasText?: boolean
  hasFaces?: boolean
  fileTypes?: string[]
}

export interface SearchOptions {
  mode: SearchMode
  query?: string
  imageFile?: Blob | ArrayBuffer | Uint8Array
  personId?: number
  filters?: SearchFilter
  limit?: number
  offset?: number
}

export interface SearchState {
  isSearching: boolean
  results: SearchResultItem[]
  totalMatches: number
  query: string
  mode: SearchMode
  filters: SearchFilter
  selectedItems: number[]
}

