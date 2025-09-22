"""FAISS vector search service for semantic and image similarity search."""

import logging
import numpy as np
import pickle
import os
from typing import List, Tuple, Dict, Any, Optional
from pathlib import Path
import threading
import time

logger = logging.getLogger(__name__)


class FAISSVectorSearchService:
    """FAISS-based vector search service for efficient similarity search."""

    def __init__(self, index_path: str = None, dimension: int = 512):
        self.dimension = dimension
        self.index_path = index_path or str(Path.home() / '.photo-search' / 'faiss_index.bin')
        self.metadata_path = self.index_path.replace('.bin', '_metadata.pkl')

        # FAISS components
        self.index = None
        self.id_to_file_id = {}  # Maps FAISS index position to file_id
        self.file_id_to_index = {}  # Maps file_id to FAISS index position

        # Thread safety
        self._lock = threading.RLock()
        self._index_dirty = False

        # Auto-save settings
        self.auto_save_threshold = 1000  # Save after this many additions
        self.unsaved_additions = 0

        # Initialize FAISS
        self._initialize_faiss()

    def _initialize_faiss(self):
        """Initialize FAISS index and load existing data if available."""
        try:
            import faiss

            # Load existing index if available
            if os.path.exists(self.index_path) and os.path.exists(self.metadata_path):
                self._load_index()
                logger.info(f"Loaded existing FAISS index with {self.index.ntotal} vectors")
            else:
                # Create new index
                self._create_new_index()
                logger.info(f"Created new FAISS index (dimension: {self.dimension})")

        except ImportError:
            raise RuntimeError("FAISS not available. Install with: pip install faiss-cpu")

    def _create_new_index(self):
        """Create a new FAISS index."""
        import faiss

        # For small collections, use flat index for exact search
        # For large collections, use IVF with PQ for approximate search
        if self.dimension == 512:  # CLIP embeddings
            # Use IndexFlatIP for cosine similarity (with normalized vectors)
            self.index = faiss.IndexFlatIP(self.dimension)
        else:
            # Generic case
            self.index = faiss.IndexFlatL2(self.dimension)

        self.id_to_file_id = {}
        self.file_id_to_index = {}

    def _should_use_ivf(self, num_vectors: int) -> bool:
        """Determine if we should switch to IVF index for better performance."""
        # Switch to IVF when we have more than 200k vectors
        return num_vectors > 200000

    def _upgrade_to_ivf_index(self):
        """Upgrade flat index to IVF index for better performance."""
        try:
            import faiss

            if self.index.ntotal == 0:
                return

            logger.info("Upgrading to IVF index for better performance")

            # Extract all vectors from current index
            all_vectors = self.index.reconstruct_n(0, self.index.ntotal)

            # Create IVF index
            nlist = min(4096, max(100, int(np.sqrt(self.index.ntotal))))
            quantizer = faiss.IndexFlatIP(self.dimension)
            ivf_index = faiss.IndexIVFPQ(quantizer, self.dimension, nlist, 64, 8)

            # Train the index
            ivf_index.train(all_vectors)

            # Add vectors to new index
            ivf_index.add(all_vectors)

            # Set search parameters
            ivf_index.nprobe = min(100, nlist // 4)

            # Replace the index
            self.index = ivf_index

            logger.info(f"Upgraded to IVF index with {nlist} clusters")

        except Exception as e:
            logger.error(f"Failed to upgrade to IVF index: {e}")

    def add_vector(self, file_id: int, vector: np.ndarray) -> bool:
        """
        Add a vector to the search index.

        Args:
            file_id: Photo file ID
            vector: Normalized embedding vector

        Returns:
            True if successful
        """
        with self._lock:
            try:
                # Validate vector
                if vector.shape != (self.dimension,):
                    logger.error(f"Vector dimension mismatch: expected {self.dimension}, got {vector.shape}")
                    return False

                # Ensure vector is normalized for cosine similarity
                norm = np.linalg.norm(vector)
                if norm > 0:
                    vector = vector / norm

                # Remove existing vector if file_id already exists
                if file_id in self.file_id_to_index:
                    self.remove_vector(file_id)

                # Add to FAISS index
                vector_2d = vector.reshape(1, -1).astype(np.float32)
                self.index.add(vector_2d)

                # Update mappings
                index_pos = self.index.ntotal - 1
                self.id_to_file_id[index_pos] = file_id
                self.file_id_to_index[file_id] = index_pos

                self.unsaved_additions += 1
                self._index_dirty = True

                # Auto-save if threshold reached
                if self.unsaved_additions >= self.auto_save_threshold:
                    self._save_index()

                # Consider upgrading to IVF if collection is large
                if (self.index.ntotal > 200000 and
                    hasattr(self.index, 'ntotal') and
                    not hasattr(self.index, 'nlist')):
                    self._upgrade_to_ivf_index()

                return True

            except Exception as e:
                logger.error(f"Failed to add vector for file_id {file_id}: {e}")
                return False

    def remove_vector(self, file_id: int) -> bool:
        """
        Remove a vector from the search index.

        Note: FAISS doesn't support efficient deletion, so we mark as deleted
        and rebuild periodically.

        Args:
            file_id: Photo file ID to remove

        Returns:
            True if successful
        """
        with self._lock:
            try:
                if file_id not in self.file_id_to_index:
                    return True  # Already removed

                index_pos = self.file_id_to_index[file_id]

                # Mark as deleted by setting file_id to None
                self.id_to_file_id[index_pos] = None
                del self.file_id_to_index[file_id]

                self._index_dirty = True

                return True

            except Exception as e:
                logger.error(f"Failed to remove vector for file_id {file_id}: {e}")
                return False

    def search(self, query_vector: np.ndarray, top_k: int = 50,
               score_threshold: float = 0.0) -> List[Tuple[int, float]]:
        """
        Search for similar vectors.

        Args:
            query_vector: Query embedding vector
            top_k: Number of results to return
            score_threshold: Minimum similarity score

        Returns:
            List of (file_id, similarity_score) tuples
        """
        with self._lock:
            try:
                if self.index.ntotal == 0:
                    return []

                # Validate and normalize query vector
                if query_vector.shape != (self.dimension,):
                    logger.error(f"Query vector dimension mismatch: expected {self.dimension}, got {query_vector.shape}")
                    return []

                norm = np.linalg.norm(query_vector)
                if norm > 0:
                    query_vector = query_vector / norm

                # Perform search
                query_2d = query_vector.reshape(1, -1).astype(np.float32)

                # Search more than needed to account for deleted entries
                search_k = min(top_k * 2, self.index.ntotal)
                similarities, indices = self.index.search(query_2d, search_k)

                # Process results
                results = []
                for i, (similarity, index_pos) in enumerate(zip(similarities[0], indices[0])):
                    if index_pos == -1:  # No more results
                        break

                    # Check if this entry is deleted
                    file_id = self.id_to_file_id.get(index_pos)
                    if file_id is None:
                        continue

                    # Apply score threshold
                    if similarity < score_threshold:
                        continue

                    results.append((file_id, float(similarity)))

                    if len(results) >= top_k:
                        break

                return results

            except Exception as e:
                logger.error(f"Search failed: {e}")
                return []

    def batch_search(self, query_vectors: np.ndarray, top_k: int = 50) -> List[List[Tuple[int, float]]]:
        """
        Batch search for multiple query vectors.

        Args:
            query_vectors: Array of query vectors (n_queries, dimension)
            top_k: Number of results per query

        Returns:
            List of search results for each query
        """
        with self._lock:
            try:
                if self.index.ntotal == 0:
                    return [[] for _ in range(len(query_vectors))]

                # Normalize query vectors
                norms = np.linalg.norm(query_vectors, axis=1, keepdims=True)
                norms[norms == 0] = 1  # Avoid division by zero
                query_vectors = query_vectors / norms

                # Perform batch search
                search_k = min(top_k * 2, self.index.ntotal)
                similarities, indices = self.index.search(query_vectors.astype(np.float32), search_k)

                # Process results
                all_results = []
                for query_idx in range(len(query_vectors)):
                    query_results = []

                    for similarity, index_pos in zip(similarities[query_idx], indices[query_idx]):
                        if index_pos == -1:
                            break

                        file_id = self.id_to_file_id.get(index_pos)
                        if file_id is None:
                            continue

                        query_results.append((file_id, float(similarity)))

                        if len(query_results) >= top_k:
                            break

                    all_results.append(query_results)

                return all_results

            except Exception as e:
                logger.error(f"Batch search failed: {e}")
                return [[] for _ in range(len(query_vectors))]

    def get_vector(self, file_id: int) -> Optional[np.ndarray]:
        """
        Get the stored vector for a file_id.

        Args:
            file_id: Photo file ID

        Returns:
            Vector if found, None otherwise
        """
        with self._lock:
            try:
                if file_id not in self.file_id_to_index:
                    return None

                index_pos = self.file_id_to_index[file_id]
                vector = self.index.reconstruct(index_pos)

                return vector

            except Exception as e:
                logger.error(f"Failed to get vector for file_id {file_id}: {e}")
                return None

    def rebuild_index(self) -> bool:
        """
        Rebuild index to remove deleted entries and optimize structure.

        Returns:
            True if successful
        """
        with self._lock:
            try:
                if self.index.ntotal == 0:
                    return True

                logger.info("Rebuilding FAISS index to remove deleted entries")

                # Collect all valid vectors and file_ids
                valid_vectors = []
                valid_file_ids = []

                for index_pos in range(self.index.ntotal):
                    file_id = self.id_to_file_id.get(index_pos)
                    if file_id is not None:
                        vector = self.index.reconstruct(index_pos)
                        valid_vectors.append(vector)
                        valid_file_ids.append(file_id)

                if not valid_vectors:
                    # Empty index
                    self._create_new_index()
                    return True

                # Create new index
                vectors_array = np.array(valid_vectors, dtype=np.float32)

                if self._should_use_ivf(len(valid_vectors)):
                    # Create IVF index
                    import faiss
                    nlist = min(4096, max(100, int(np.sqrt(len(valid_vectors)))))
                    quantizer = faiss.IndexFlatIP(self.dimension)
                    new_index = faiss.IndexIVFPQ(quantizer, self.dimension, nlist, 64, 8)
                    new_index.train(vectors_array)
                    new_index.add(vectors_array)
                    new_index.nprobe = min(100, nlist // 4)
                else:
                    # Create flat index
                    import faiss
                    new_index = faiss.IndexFlatIP(self.dimension)
                    new_index.add(vectors_array)

                # Update mappings
                new_id_to_file_id = {}
                new_file_id_to_index = {}

                for i, file_id in enumerate(valid_file_ids):
                    new_id_to_file_id[i] = file_id
                    new_file_id_to_index[file_id] = i

                # Replace index and mappings
                self.index = new_index
                self.id_to_file_id = new_id_to_file_id
                self.file_id_to_index = new_file_id_to_index

                self._index_dirty = True
                self._save_index()

                logger.info(f"Index rebuilt with {len(valid_vectors)} vectors")

                return True

            except Exception as e:
                logger.error(f"Failed to rebuild index: {e}")
                return False

    def save_index(self) -> bool:
        """
        Save index to disk.

        Returns:
            True if successful
        """
        with self._lock:
            return self._save_index()

    def _save_index(self) -> bool:
        """Internal method to save index."""
        try:
            if not self._index_dirty:
                return True

            # Ensure directory exists
            os.makedirs(os.path.dirname(self.index_path), exist_ok=True)

            # Save FAISS index
            import faiss
            faiss.write_index(self.index, self.index_path)

            # Save metadata
            metadata = {
                'id_to_file_id': self.id_to_file_id,
                'file_id_to_index': self.file_id_to_index,
                'dimension': self.dimension,
                'saved_at': time.time()
            }

            with open(self.metadata_path, 'wb') as f:
                pickle.dump(metadata, f)

            self._index_dirty = False
            self.unsaved_additions = 0

            logger.debug(f"FAISS index saved to {self.index_path}")

            return True

        except Exception as e:
            logger.error(f"Failed to save index: {e}")
            return False

    def _load_index(self) -> bool:
        """Load index from disk."""
        try:
            import faiss

            # Load FAISS index
            self.index = faiss.read_index(self.index_path)

            # Load metadata
            with open(self.metadata_path, 'rb') as f:
                metadata = pickle.load(f)

            self.id_to_file_id = metadata['id_to_file_id']
            self.file_id_to_index = metadata['file_id_to_index']

            # Verify dimension consistency
            if metadata.get('dimension', self.dimension) != self.dimension:
                logger.warning(f"Dimension mismatch: expected {self.dimension}, got {metadata.get('dimension')}")

            self._index_dirty = False
            self.unsaved_additions = 0

            return True

        except Exception as e:
            logger.error(f"Failed to load index: {e}")
            return False

    def get_statistics(self) -> Dict[str, Any]:
        """Get index statistics."""
        with self._lock:
            total_vectors = self.index.ntotal if self.index else 0
            valid_vectors = len(self.file_id_to_index)
            deleted_vectors = total_vectors - valid_vectors

            stats = {
                'total_vectors': total_vectors,
                'valid_vectors': valid_vectors,
                'deleted_vectors': deleted_vectors,
                'dimension': self.dimension,
                'index_type': type(self.index).__name__ if self.index else None,
                'index_dirty': self._index_dirty,
                'unsaved_additions': self.unsaved_additions
            }

            # Add IVF-specific stats if applicable
            if hasattr(self.index, 'nlist'):
                stats['nlist'] = self.index.nlist
                stats['nprobe'] = getattr(self.index, 'nprobe', None)

            return stats

    def cleanup(self):
        """Cleanup resources and save index."""
        with self._lock:
            if self._index_dirty:
                self._save_index()


# Global instance
_vector_search_service: Optional[FAISSVectorSearchService] = None


def get_vector_search_service() -> FAISSVectorSearchService:
    """Get or create the global vector search service instance."""
    global _vector_search_service
    if _vector_search_service is None:
        _vector_search_service = FAISSVectorSearchService()
    return _vector_search_service


def initialize_vector_search_service(index_path: str = None, dimension: int = 512) -> FAISSVectorSearchService:
    """Initialize vector search service with custom parameters."""
    global _vector_search_service
    _vector_search_service = FAISSVectorSearchService(index_path, dimension)
    return _vector_search_service