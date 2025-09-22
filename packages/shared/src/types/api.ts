/**
 * API request/response types
 */

import { Person } from './models'

// Common response wrapper
export interface ApiResponse<T = any> {
  data?: T
  error?: string
  message?: string
}

// Health check
export interface HealthResponse {
  status: 'healthy'
  timestamp: string
}

// Configuration
export interface Configuration {
  roots: string[]
  ocr_languages: string[]
  face_search_enabled: boolean
  index_version: string
}

export interface UpdateRootsRequest {
  roots: string[]
}

// Indexing
export interface StartIndexingRequest {
  full?: boolean
}

export interface IndexStatus {
  status: 'idle' | 'indexing' | 'error'
  progress?: {
    total_files: number
    processed_files: number
    current_phase: 'discovery' | 'metadata' | 'ocr' | 'embeddings' | 'faces'
  }
  errors?: string[]
  started_at?: string
  estimated_completion?: string
}

// Search
export interface SearchParams {
  q?: string
  from?: string // YYYY-MM-DD
  to?: string // YYYY-MM-DD
  folder?: string
  limit?: number
  offset?: number
}

export interface SemanticSearchRequest {
  text: string
  top_k?: number
}

export interface ImageSearchRequest {
  file: File
  top_k?: number
}

export interface FaceSearchRequest {
  person_id: number
  top_k?: number
}

export interface SearchResultItem {
  file_id: number
  path: string
  folder: string
  filename: string
  thumb_path?: string
  shot_dt?: string
  score: number
  badges: ('OCR' | 'Face' | 'Photo-Match' | 'EXIF')[]
  snippet?: string
}

export interface SearchResults {
  query: string
  total_matches: number
  items: SearchResultItem[]
  took_ms: number
}

// People management
export interface CreatePersonRequest {
  name: string
  sample_file_ids: number[]
}

export interface PersonResponse extends Person {
  // Additional fields for API response
}