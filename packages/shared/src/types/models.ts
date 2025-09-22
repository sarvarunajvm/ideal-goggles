/**
 * Data model types for photo search application
 */

export interface Photo {
  id: number
  path: string
  folder: string
  filename: string
  ext: string
  size: number
  created_ts: number
  modified_ts: number
  sha1: string
  phash?: string
  indexed_at?: number
  index_version: number
}

export interface ExifData {
  file_id: number
  shot_dt?: string
  camera_make?: string
  camera_model?: string
  lens?: string
  iso?: number
  aperture?: number
  shutter_speed?: string
  focal_length?: number
  gps_lat?: number
  gps_lon?: number
  orientation?: number
}

export interface OcrData {
  file_id: number
  text: string
  language: string
  confidence: number
  processed_at: number
}

export interface Embedding {
  file_id: number
  clip_vector: number[]
  embedding_model: string
  processed_at: number
}

export interface Person {
  id: number
  name: string
  face_vector: number[]
  sample_count: number
  created_at: number
  updated_at: number
  active: boolean
}

export interface FaceDetection {
  id: number
  file_id: number
  person_id?: number
  box_xyxy: [number, number, number, number]
  face_vector: number[]
  confidence: number
  verified: boolean
}

export interface Thumbnail {
  file_id: number
  thumb_path: string
  width: number
  height: number
  format: string
  generated_at: number
}

export interface DriveAlias {
  device_id: string
  alias: string
  mount_point?: string
  last_seen: number
}