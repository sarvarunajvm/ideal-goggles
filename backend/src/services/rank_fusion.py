"""Rank fusion service for combining multiple search result types."""

import logging
import math
from typing import List, Dict, Any, Tuple, Optional, Set
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class SearchType(Enum):
    """Types of search results that can be fused."""
    TEXT = "text"
    SEMANTIC = "semantic"
    IMAGE = "image"
    FACE = "face"
    METADATA = "metadata"


@dataclass
class SearchResult:
    """Individual search result with score and metadata."""
    file_id: int
    score: float
    search_type: SearchType
    metadata: Dict[str, Any]
    rank: int = 0


@dataclass
class FusionWeights:
    """Weights for different search types in fusion."""
    text: float = 1.0
    semantic: float = 0.8
    image: float = 0.9
    face: float = 0.7
    metadata: float = 0.5


class RankFusionService:
    """Service for combining and ranking multiple search result types."""

    def __init__(self, default_weights: Optional[FusionWeights] = None):
        self.default_weights = default_weights or FusionWeights()

    def fuse_results(
        self,
        result_sets: Dict[SearchType, List[SearchResult]],
        weights: Optional[FusionWeights] = None,
        method: str = "rrf",  # Reciprocal Rank Fusion
        k: float = 60.0,  # RRF parameter
        top_k: int = 50
    ) -> List[SearchResult]:
        """
        Fuse multiple sets of search results into a single ranked list.

        Args:
            result_sets: Dictionary mapping search types to their results
            weights: Weights for different search types
            method: Fusion method ('rrf', 'weighted_sum', 'borda_count')
            k: Parameter for RRF method
            top_k: Number of results to return

        Returns:
            Fused and ranked search results
        """
        if not result_sets:
            return []

        weights = weights or self.default_weights

        try:
            if method == "rrf":
                return self._reciprocal_rank_fusion(result_sets, weights, k, top_k)
            elif method == "weighted_sum":
                return self._weighted_sum_fusion(result_sets, weights, top_k)
            elif method == "borda_count":
                return self._borda_count_fusion(result_sets, weights, top_k)
            else:
                logger.warning(f"Unknown fusion method: {method}, using RRF")
                return self._reciprocal_rank_fusion(result_sets, weights, k, top_k)

        except Exception as e:
            logger.error(f"Rank fusion failed: {e}")
            # Fallback: return first non-empty result set
            for results in result_sets.values():
                if results:
                    return results[:top_k]
            return []

    def _reciprocal_rank_fusion(
        self,
        result_sets: Dict[SearchType, List[SearchResult]],
        weights: FusionWeights,
        k: float,
        top_k: int
    ) -> List[SearchResult]:
        """
        Reciprocal Rank Fusion (RRF) algorithm.

        RRF Score = sum(weight / (k + rank)) for each search type
        """
        # Collect all unique file IDs
        all_file_ids: Set[int] = set()
        for results in result_sets.values():
            all_file_ids.update(result.file_id for result in results)

        # Calculate RRF scores
        fused_scores: Dict[int, float] = {}
        result_metadata: Dict[int, Dict[str, Any]] = {}

        for file_id in all_file_ids:
            rrf_score = 0.0
            combined_metadata = {}

            for search_type, results in result_sets.items():
                weight = self._get_weight_for_type(search_type, weights)

                # Find this file_id in the results
                for rank, result in enumerate(results, 1):
                    if result.file_id == file_id:
                        rrf_contribution = weight / (k + rank)
                        rrf_score += rrf_contribution

                        # Combine metadata
                        combined_metadata[f"{search_type.value}_score"] = result.score
                        combined_metadata[f"{search_type.value}_rank"] = rank
                        combined_metadata.update(result.metadata)
                        break

            fused_scores[file_id] = rrf_score
            result_metadata[file_id] = combined_metadata

        # Sort by fused score and create result objects
        sorted_file_ids = sorted(
            fused_scores.keys(),
            key=lambda fid: fused_scores[fid],
            reverse=True
        )

        fused_results = []
        for rank, file_id in enumerate(sorted_file_ids[:top_k], 1):
            result = SearchResult(
                file_id=file_id,
                score=fused_scores[file_id],
                search_type=SearchType.TEXT,  # Default type for fused results
                metadata=result_metadata[file_id],
                rank=rank
            )
            fused_results.append(result)

        return fused_results

    def _weighted_sum_fusion(
        self,
        result_sets: Dict[SearchType, List[SearchResult]],
        weights: FusionWeights,
        top_k: int
    ) -> List[SearchResult]:
        """
        Weighted sum fusion using normalized scores.
        """
        # Normalize scores within each result set
        normalized_sets = {}
        for search_type, results in result_sets.items():
            if not results:
                continue

            # Normalize scores to [0, 1] range
            max_score = max(result.score for result in results)
            min_score = min(result.score for result in results)
            score_range = max_score - min_score

            normalized_results = []
            for result in results:
                if score_range > 0:
                    normalized_score = (result.score - min_score) / score_range
                else:
                    normalized_score = 1.0

                normalized_results.append(SearchResult(
                    file_id=result.file_id,
                    score=normalized_score,
                    search_type=result.search_type,
                    metadata=result.metadata
                ))

            normalized_sets[search_type] = normalized_results

        # Calculate weighted sum scores
        all_file_ids: Set[int] = set()
        for results in normalized_sets.values():
            all_file_ids.update(result.file_id for result in results)

        weighted_scores: Dict[int, float] = {}
        result_metadata: Dict[int, Dict[str, Any]] = {}

        for file_id in all_file_ids:
            total_score = 0.0
            combined_metadata = {}

            for search_type, results in normalized_sets.items():
                weight = self._get_weight_for_type(search_type, weights)

                for result in results:
                    if result.file_id == file_id:
                        weighted_contribution = result.score * weight
                        total_score += weighted_contribution

                        combined_metadata[f"{search_type.value}_score"] = result.score
                        combined_metadata.update(result.metadata)
                        break

            weighted_scores[file_id] = total_score
            result_metadata[file_id] = combined_metadata

        # Sort and create results
        sorted_file_ids = sorted(
            weighted_scores.keys(),
            key=lambda fid: weighted_scores[fid],
            reverse=True
        )

        fused_results = []
        for rank, file_id in enumerate(sorted_file_ids[:top_k], 1):
            result = SearchResult(
                file_id=file_id,
                score=weighted_scores[file_id],
                search_type=SearchType.TEXT,
                metadata=result_metadata[file_id],
                rank=rank
            )
            fused_results.append(result)

        return fused_results

    def _borda_count_fusion(
        self,
        result_sets: Dict[SearchType, List[SearchResult]],
        weights: FusionWeights,
        top_k: int
    ) -> List[SearchResult]:
        """
        Borda count fusion using rank positions.
        """
        all_file_ids: Set[int] = set()
        for results in result_sets.values():
            all_file_ids.update(result.file_id for result in results)

        borda_scores: Dict[int, float] = {}
        result_metadata: Dict[int, Dict[str, Any]] = {}

        for file_id in all_file_ids:
            total_borda_score = 0.0
            combined_metadata = {}

            for search_type, results in result_sets.items():
                weight = self._get_weight_for_type(search_type, weights)
                max_rank = len(results)

                for rank, result in enumerate(results):
                    if result.file_id == file_id:
                        # Borda count: higher rank = lower position number
                        borda_contribution = weight * (max_rank - rank)
                        total_borda_score += borda_contribution

                        combined_metadata[f"{search_type.value}_score"] = result.score
                        combined_metadata[f"{search_type.value}_rank"] = rank + 1
                        combined_metadata.update(result.metadata)
                        break

            borda_scores[file_id] = total_borda_score
            result_metadata[file_id] = combined_metadata

        # Sort and create results
        sorted_file_ids = sorted(
            borda_scores.keys(),
            key=lambda fid: borda_scores[fid],
            reverse=True
        )

        fused_results = []
        for rank, file_id in enumerate(sorted_file_ids[:top_k], 1):
            result = SearchResult(
                file_id=file_id,
                score=borda_scores[file_id],
                search_type=SearchType.TEXT,
                metadata=result_metadata[file_id],
                rank=rank
            )
            fused_results.append(result)

        return fused_results

    def _get_weight_for_type(self, search_type: SearchType, weights: FusionWeights) -> float:
        """Get weight for a specific search type."""
        weight_map = {
            SearchType.TEXT: weights.text,
            SearchType.SEMANTIC: weights.semantic,
            SearchType.IMAGE: weights.image,
            SearchType.FACE: weights.face,
            SearchType.METADATA: weights.metadata
        }
        return weight_map.get(search_type, 1.0)

    def analyze_fusion_quality(
        self,
        result_sets: Dict[SearchType, List[SearchResult]],
        fused_results: List[SearchResult],
        top_k: int = 20
    ) -> Dict[str, Any]:
        """
        Analyze the quality of fusion results.

        Args:
            result_sets: Original result sets
            fused_results: Fused results
            top_k: Number of top results to analyze

        Returns:
            Quality analysis metrics
        """
        try:
            analysis = {
                'input_sets': len(result_sets),
                'total_unique_results': 0,
                'fusion_coverage': {},
                'rank_correlation': {},
                'diversity_score': 0.0
            }

            # Calculate total unique results
            all_file_ids = set()
            for results in result_sets.values():
                all_file_ids.update(result.file_id for result in results)
            analysis['total_unique_results'] = len(all_file_ids)

            # Calculate coverage: how many top results from each set made it to fused top-k
            top_fused_ids = set(result.file_id for result in fused_results[:top_k])

            for search_type, results in result_sets.items():
                if not results:
                    continue

                top_original_ids = set(result.file_id for result in results[:top_k])
                coverage = len(top_fused_ids.intersection(top_original_ids)) / len(top_original_ids)
                analysis['fusion_coverage'][search_type.value] = round(coverage, 3)

            # Calculate diversity: how many different search types contributed to top results
            contributing_types = set()
            for result in fused_results[:top_k]:
                for search_type in result_sets.keys():
                    if f"{search_type.value}_score" in result.metadata:
                        contributing_types.add(search_type)

            analysis['diversity_score'] = len(contributing_types) / len(result_sets) if result_sets else 0

            # Calculate rank correlation (simplified)
            if len(result_sets) >= 2:
                type_pairs = list(result_sets.keys())[:2]
                correlation = self._calculate_rank_correlation(
                    result_sets[type_pairs[0]][:top_k],
                    result_sets[type_pairs[1]][:top_k]
                )
                analysis['rank_correlation'] = {
                    f"{type_pairs[0].value}_vs_{type_pairs[1].value}": round(correlation, 3)
                }

            return analysis

        except Exception as e:
            logger.error(f"Fusion quality analysis failed: {e}")
            return {}

    def _calculate_rank_correlation(self, results1: List[SearchResult], results2: List[SearchResult]) -> float:
        """Calculate rank correlation between two result sets."""
        try:
            # Create rank mappings
            rank1 = {result.file_id: rank for rank, result in enumerate(results1)}
            rank2 = {result.file_id: rank for rank, result in enumerate(results2)}

            # Find common file IDs
            common_ids = set(rank1.keys()).intersection(set(rank2.keys()))

            if len(common_ids) < 2:
                return 0.0

            # Calculate Spearman's rank correlation
            rank_diffs = []
            for file_id in common_ids:
                diff = rank1[file_id] - rank2[file_id]
                rank_diffs.append(diff * diff)

            n = len(common_ids)
            sum_diff_squared = sum(rank_diffs)

            # Spearman's correlation coefficient
            correlation = 1 - (6 * sum_diff_squared) / (n * (n * n - 1))

            return correlation

        except Exception:
            return 0.0

    def get_fusion_recommendations(
        self,
        query_type: str,
        user_preferences: Optional[Dict[str, float]] = None
    ) -> Tuple[FusionWeights, str]:
        """
        Get recommended fusion weights and method based on query type and user preferences.

        Args:
            query_type: Type of query ('text', 'image', 'person', 'mixed')
            user_preferences: User-specific weight preferences

        Returns:
            Tuple of (recommended_weights, recommended_method)
        """
        # Default recommendations based on query type
        weight_recommendations = {
            'text': FusionWeights(text=1.0, semantic=0.6, image=0.3, face=0.2, metadata=0.8),
            'image': FusionWeights(text=0.4, semantic=0.9, image=1.0, face=0.3, metadata=0.5),
            'person': FusionWeights(text=0.3, semantic=0.5, image=0.6, face=1.0, metadata=0.4),
            'mixed': FusionWeights(text=0.8, semantic=0.8, image=0.8, face=0.6, metadata=0.6)
        }

        recommended_weights = weight_recommendations.get(query_type, self.default_weights)

        # Apply user preferences if provided
        if user_preferences:
            recommended_weights = FusionWeights(
                text=user_preferences.get('text', recommended_weights.text),
                semantic=user_preferences.get('semantic', recommended_weights.semantic),
                image=user_preferences.get('image', recommended_weights.image),
                face=user_preferences.get('face', recommended_weights.face),
                metadata=user_preferences.get('metadata', recommended_weights.metadata)
            )

        # Method recommendations
        method_recommendations = {
            'text': 'weighted_sum',
            'image': 'rrf',
            'person': 'rrf',
            'mixed': 'rrf'
        }

        recommended_method = method_recommendations.get(query_type, 'rrf')

        return recommended_weights, recommended_method


# Global instance
_rank_fusion_service: Optional[RankFusionService] = None


def get_rank_fusion_service() -> RankFusionService:
    """Get or create the global rank fusion service instance."""
    global _rank_fusion_service
    if _rank_fusion_service is None:
        _rank_fusion_service = RankFusionService()
    return _rank_fusion_service


def create_search_result(
    file_id: int,
    score: float,
    search_type: SearchType,
    **metadata
) -> SearchResult:
    """Helper function to create SearchResult objects."""
    return SearchResult(
        file_id=file_id,
        score=score,
        search_type=search_type,
        metadata=metadata
    )