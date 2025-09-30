"""CLIP embedding worker for semantic image search."""

import asyncio
import logging
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Any

import numpy as np

from ..models.embedding import Embedding, EmbeddingStats
from ..models.photo import Photo

logger = logging.getLogger(__name__)


class CLIPEmbeddingWorker:
    """Worker for generating CLIP embeddings from images."""

    def __init__(self, max_workers: int = 2, model_name: str = "ViT-B/32"):
        self.max_workers = max_workers
        self.model_name = model_name
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.stats = EmbeddingStats()

        # CLIP model components
        self.model = None
        self.preprocess = None
        self.device = None

        # Initialize CLIP model
        self._initialize_clip_model()

    def _initialize_clip_model(self):
        """Initialize CLIP model for embedding generation."""
        try:
            import clip
            import torch

            # Determine device
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
            logger.info(f"Using device: {self.device}")

            # Load CLIP model
            self.model, self.preprocess = clip.load(self.model_name, device=self.device)
            self.model.eval()

            logger.info(f"CLIP model loaded: {self.model_name}")

        except ImportError as e:
            msg = f"CLIP dependencies not installed: {e}"
            raise RuntimeError(msg)
        except Exception as e:
            msg = f"Failed to initialize CLIP model: {e}"
            raise RuntimeError(msg)

    async def generate_embedding(self, photo: Photo) -> Embedding | None:
        """Generate CLIP embedding for a photo."""
        start_time = time.time()

        try:
            # Run embedding generation in thread pool
            loop = asyncio.get_event_loop()
            embedding_vector = await loop.run_in_executor(
                self.executor, self._generate_embedding_sync, photo.path
            )

            processing_time = time.time() - start_time

            if embedding_vector is not None:
                embedding = Embedding.from_clip_output(
                    photo.id, embedding_vector, self.model_name
                )

                self.stats.add_embedding(embedding, processing_time)
                logger.debug(
                    f"Generated embedding for {photo.path} (dim: {len(embedding_vector)})"
                )
                return embedding
            return None

        except Exception as e:
            logger.warning(f"Embedding generation failed for {photo.path}: {e}")
            return None

    def _generate_embedding_sync(self, file_path: str) -> np.ndarray | None:
        """Synchronously generate CLIP embedding."""
        try:
            import torch
            from PIL import Image

            # Load and preprocess image
            with Image.open(file_path) as img:
                # Convert to RGB if necessary
                if img.mode != "RGB":
                    img = img.convert("RGB")

                # Preprocess image
                image_tensor = self.preprocess(img).unsqueeze(0).to(self.device)

            # Generate embedding
            with torch.no_grad():
                image_features = self.model.encode_image(image_tensor)

                # Normalize features
                image_features = image_features / image_features.norm(
                    dim=-1, keepdim=True
                )

                # Convert to numpy
                embedding = image_features.cpu().numpy().flatten()

            return embedding.astype(np.float32)

        except Exception as e:
            logger.debug(f"CLIP embedding generation failed for {file_path}: {e}")
            return None

    async def generate_text_embedding(self, text: str) -> np.ndarray | None:
        """Generate CLIP embedding for text query."""
        try:
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(
                self.executor, self._generate_text_embedding_sync, text
            )

        except Exception as e:
            logger.warning(f"Text embedding generation failed: {e}")
            return None

    def _generate_text_embedding_sync(self, text: str) -> np.ndarray | None:
        """Synchronously generate CLIP text embedding."""
        try:
            import clip
            import torch

            # Tokenize text
            text_tokens = clip.tokenize([text]).to(self.device)

            # Generate embedding
            with torch.no_grad():
                text_features = self.model.encode_text(text_tokens)

                # Normalize features
                text_features = text_features / text_features.norm(dim=-1, keepdim=True)

                # Convert to numpy
                embedding = text_features.cpu().numpy().flatten()

            return embedding.astype(np.float32)

        except Exception as e:
            logger.debug(f"Text embedding generation failed: {e}")
            return None

    async def generate_batch(
        self, photos: list[Photo], batch_size: int = 8
    ) -> list[Embedding | None]:
        """Generate embeddings for multiple photos in batches."""
        if not photos:
            return []

        logger.info(f"Generating embeddings for {len(photos)} photos")

        results = []

        # Process in batches to manage memory
        for i in range(0, len(photos), batch_size):
            batch = photos[i : i + batch_size]

            # Create tasks for concurrent processing
            tasks = [self.generate_embedding(photo) for photo in batch]

            # Process batch
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)

            # Handle results and exceptions
            for j, result in enumerate(batch_results):
                if isinstance(result, Exception):
                    logger.warning(f"Embedding failed for {batch[j].path}: {result}")
                    results.append(None)
                else:
                    results.append(result)

            # Log progress
            logger.info(
                f"Embedding progress: {min(i + batch_size, len(photos))}/{len(photos)}"
            )

            # Small delay between batches to prevent overload
            await asyncio.sleep(0.1)

        successful_count = len([r for r in results if r])
        logger.info(
            f"Embedding generation completed: {successful_count}/{len(photos)} successful"
        )

        return results

    def get_statistics(self) -> dict[str, Any]:
        """Get embedding generation statistics."""
        stats_dict = self.stats.to_dict()
        stats_dict.update(
            {
                "model_name": self.model_name,
                "device": str(self.device),
                "max_workers": self.max_workers,
            }
        )
        return stats_dict

    def reset_statistics(self):
        """Reset embedding statistics."""
        self.stats = EmbeddingStats()

    def shutdown(self):
        """Shutdown the executor and clean up resources."""
        self.executor.shutdown(wait=True)

        # Clear CUDA cache if using GPU
        try:
            import torch

            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        except ImportError:
            pass


class OptimizedCLIPWorker(CLIPEmbeddingWorker):
    """Optimized CLIP worker with batched processing and caching."""

    def __init__(
        self,
        max_workers: int = 2,
        model_name: str = "ViT-B/32",
        enable_batch_processing: bool = True,
        cache_size: int = 1000,
    ):
        super().__init__(max_workers, model_name)
        self.enable_batch_processing = enable_batch_processing
        self.cache_size = cache_size
        self.embedding_cache = {}

    async def generate_batch_optimized(
        self, photos: list[Photo], batch_size: int = 16
    ) -> list[Embedding | None]:
        """Optimized batch processing with actual batching in GPU."""
        if not photos or not self.enable_batch_processing:
            return await self.generate_batch(photos, batch_size)

        logger.info(f"Generating embeddings for {len(photos)} photos (optimized)")

        results = []

        # Process in GPU batches
        for i in range(0, len(photos), batch_size):
            batch_photos = photos[i : i + batch_size]

            # Check cache first
            cached_results = []
            uncached_photos = []
            uncached_indices = []

            for j, photo in enumerate(batch_photos):
                cache_key = f"{photo.path}:{photo.modified_ts}"
                if cache_key in self.embedding_cache:
                    cached_results.append((j, self.embedding_cache[cache_key]))
                else:
                    uncached_photos.append(photo)
                    uncached_indices.append(j)

            # Process uncached photos in actual batch
            batch_embeddings = []
            if uncached_photos:
                batch_embeddings = await self._process_batch_on_gpu(uncached_photos)

            # Combine cached and new results
            batch_results = [None] * len(batch_photos)

            # Fill cached results
            for idx, embedding in cached_results:
                batch_results[idx] = embedding

            # Fill new results and update cache
            for idx, embedding in zip(uncached_indices, batch_embeddings, strict=False):
                batch_results[idx] = embedding
                if embedding:
                    cache_key = (
                        f"{batch_photos[idx].path}:{batch_photos[idx].modified_ts}"
                    )
                    self._update_cache(cache_key, embedding)

            results.extend(batch_results)

            # Log progress
            logger.info(
                f"Optimized embedding progress: {min(i + batch_size, len(photos))}/{len(photos)}"
            )

        successful_count = len([r for r in results if r])
        logger.info(
            f"Optimized embedding completed: {successful_count}/{len(photos)} successful"
        )

        # Save embeddings to database
        if successful_count > 0:
            self._save_embeddings_to_database(results)

        return results

    async def _process_batch_on_gpu(
        self, photos: list[Photo]
    ) -> list[Embedding | None]:
        """Process a batch of photos on GPU simultaneously."""
        try:
            loop = asyncio.get_event_loop()
            embeddings = await loop.run_in_executor(
                self.executor,
                self._generate_batch_embeddings_sync,
                [photo.path for photo in photos],
            )

            # Convert to Embedding objects
            results = []
            for _i, (photo, embedding_vector) in enumerate(
                zip(photos, embeddings, strict=False)
            ):
                if embedding_vector is not None:
                    embedding = Embedding.from_clip_output(
                        photo.id, embedding_vector, self.model_name
                    )
                    self.stats.add_embedding(embedding)
                    results.append(embedding)
                else:
                    results.append(None)

            return results

        except Exception as e:
            logger.warning(f"Batch GPU processing failed: {e}")
            # Fallback to individual processing
            return [await self.generate_embedding(photo) for photo in photos]

    def _generate_batch_embeddings_sync(
        self, file_paths: list[str]
    ) -> list[np.ndarray | None]:
        """Generate embeddings for a batch of images on GPU."""
        try:
            import torch
            from PIL import Image

            # Load and preprocess all images
            image_tensors = []
            valid_indices = []

            for i, file_path in enumerate(file_paths):
                try:
                    with Image.open(file_path) as img:
                        if img.mode != "RGB":
                            img = img.convert("RGB")

                        image_tensor = self.preprocess(img)
                        image_tensors.append(image_tensor)
                        valid_indices.append(i)

                except Exception as e:
                    logger.debug(f"Failed to load image {file_path}: {e}")

            if not image_tensors:
                return [None] * len(file_paths)

            # Stack tensors into batch
            batch_tensor = torch.stack(image_tensors).to(self.device)

            # Generate embeddings for the entire batch
            with torch.no_grad():
                batch_features = self.model.encode_image(batch_tensor)

                # Normalize features
                batch_features = batch_features / batch_features.norm(
                    dim=-1, keepdim=True
                )

                # Convert to numpy
                batch_embeddings = batch_features.cpu().numpy()

            # Map results back to original indices
            results = [None] * len(file_paths)
            for i, valid_idx in enumerate(valid_indices):
                results[valid_idx] = batch_embeddings[i].astype(np.float32)

            return results

        except Exception as e:
            logger.debug(f"Batch embedding generation failed: {e}")
            return [None] * len(file_paths)

    def _update_cache(self, cache_key: str, embedding: Embedding):
        """Update embedding cache with size limit."""
        if len(self.embedding_cache) >= self.cache_size:
            # Remove oldest entry (simple FIFO)
            oldest_key = next(iter(self.embedding_cache))
            del self.embedding_cache[oldest_key]

        self.embedding_cache[cache_key] = embedding

    def clear_cache(self):
        """Clear the embedding cache."""
        self.embedding_cache.clear()

    def _save_embeddings_to_database(self, embeddings: list[Embedding | None]):
        """Save generated embeddings to database."""
        try:
            from ..db.connection import get_database_manager

            db_manager = get_database_manager()
            saved_count = 0

            for embedding in embeddings:
                if embedding:
                    try:
                        # Convert numpy array to blob
                        vector_blob = embedding._numpy_to_blob(embedding.clip_vector)

                        # Save to database
                        with db_manager.get_transaction() as conn:
                            conn.execute(
                                """
                                INSERT OR REPLACE INTO embeddings
                                (file_id, clip_vector, embedding_model, processed_at)
                                VALUES (?, ?, ?, ?)
                                """,
                                (
                                    embedding.file_id,
                                    vector_blob,
                                    embedding.embedding_model,
                                    embedding.processed_at,
                                ),
                            )
                        saved_count += 1
                    except Exception as e:
                        logger.warning(
                            f"Failed to save embedding for file_id {embedding.file_id}: {e}"
                        )

            logger.info(f"Saved {saved_count} embeddings to database")

        except Exception as e:
            logger.exception(f"Failed to save embeddings to database: {e}")

    def get_cache_statistics(self) -> dict[str, Any]:
        """Get cache statistics."""
        return {
            "cache_size": len(self.embedding_cache),
            "cache_limit": self.cache_size,
            "cache_hit_rate": 0.0,  # Would need tracking to calculate
        }


class EmbeddingValidator:
    """Validator for embedding quality and consistency."""

    @staticmethod
    def validate_embedding(embedding: Embedding) -> dict[str, Any]:
        """Validate embedding quality."""
        validation_result = {
            "is_valid": embedding.is_valid(),
            "errors": embedding.validate(),
            "dimension": embedding.get_dimension(),
            "norm": embedding.get_norm(),
            "is_normalized": embedding.is_normalized(),
            "stats": embedding.get_vector_stats(),
        }

        # Quality checks
        stats = embedding.get_vector_stats()

        # Check for reasonable value distribution
        if abs(stats["mean"]) > 0.5:
            validation_result["warnings"] = validation_result.get("warnings", [])
            validation_result["warnings"].append("Mean value seems too high")

        if stats["std"] < 0.1:
            validation_result["warnings"] = validation_result.get("warnings", [])
            validation_result["warnings"].append(
                "Low standard deviation may indicate poor feature extraction"
            )

        return validation_result

    @staticmethod
    def compare_embeddings(
        embedding1: Embedding, embedding2: Embedding
    ) -> dict[str, Any]:
        """Compare two embeddings for consistency."""
        if embedding1.embedding_model != embedding2.embedding_model:
            return {"comparable": False, "reason": "Different embedding models"}

        similarity = embedding1.cosine_similarity(embedding2)
        distance = embedding1.euclidean_distance(embedding2)

        return {
            "comparable": True,
            "cosine_similarity": similarity,
            "euclidean_distance": distance,
            "dimension_match": embedding1.get_dimension() == embedding2.get_dimension(),
            "model_match": embedding1.embedding_model == embedding2.embedding_model,
        }
