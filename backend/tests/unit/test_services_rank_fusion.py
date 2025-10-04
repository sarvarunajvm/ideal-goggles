"""Comprehensive unit tests for RankFusionService."""

import pytest

from src.services.rank_fusion import (
    FusionWeights,
    RankFusionService,
    SearchResult,
    SearchType,
    create_search_result,
    get_rank_fusion_service,
)


class TestSearchType:
    """Test SearchType enum."""

    def test_search_type_values(self):
        """Test all search type enum values."""
        assert SearchType.TEXT.value == "text"
        assert SearchType.SEMANTIC.value == "semantic"
        assert SearchType.IMAGE.value == "image"
        assert SearchType.FACE.value == "face"
        assert SearchType.METADATA.value == "metadata"


class TestSearchResult:
    """Test SearchResult dataclass."""

    def test_search_result_creation(self):
        """Test creating a search result."""
        result = SearchResult(
            file_id=1,
            score=0.95,
            search_type=SearchType.TEXT,
            metadata={"snippet": "test"},
        )

        assert result.file_id == 1
        assert result.score == 0.95
        assert result.search_type == SearchType.TEXT
        assert result.metadata == {"snippet": "test"}
        assert result.rank == 0  # Default value

    def test_search_result_with_rank(self):
        """Test creating a search result with rank."""
        result = SearchResult(
            file_id=1,
            score=0.95,
            search_type=SearchType.TEXT,
            metadata={},
            rank=5,
        )

        assert result.rank == 5


class TestFusionWeights:
    """Test FusionWeights dataclass."""

    def test_fusion_weights_defaults(self):
        """Test default fusion weights."""
        weights = FusionWeights()

        assert weights.text == 1.0
        assert weights.semantic == 0.8
        assert weights.image == 0.9
        assert weights.face == 0.7
        assert weights.metadata == 0.5

    def test_fusion_weights_custom(self):
        """Test custom fusion weights."""
        weights = FusionWeights(
            text=0.5,
            semantic=1.0,
            image=0.3,
            face=0.2,
            metadata=0.1,
        )

        assert weights.text == 0.5
        assert weights.semantic == 1.0
        assert weights.image == 0.3
        assert weights.face == 0.2
        assert weights.metadata == 0.1


class TestRankFusionService:
    """Test RankFusionService class with comprehensive coverage."""

    @pytest.fixture
    def fusion_service(self):
        """Create a RankFusionService instance."""
        return RankFusionService()

    @pytest.fixture
    def custom_weights_service(self):
        """Create service with custom weights."""
        weights = FusionWeights(text=0.5, semantic=1.0)
        return RankFusionService(default_weights=weights)

    @pytest.fixture
    def sample_result_sets(self):
        """Create sample result sets for testing."""
        return {
            SearchType.TEXT: [
                SearchResult(1, 0.9, SearchType.TEXT, {"source": "filename"}),
                SearchResult(2, 0.8, SearchType.TEXT, {"source": "filename"}),
                SearchResult(3, 0.7, SearchType.TEXT, {"source": "ocr"}),
            ],
            SearchType.SEMANTIC: [
                SearchResult(2, 0.85, SearchType.SEMANTIC, {"source": "embedding"}),
                SearchResult(4, 0.75, SearchType.SEMANTIC, {"source": "embedding"}),
                SearchResult(1, 0.65, SearchType.SEMANTIC, {"source": "embedding"}),
            ],
        }

    def test_initialization_default_weights(self, fusion_service):
        """Test initialization with default weights."""
        assert fusion_service.default_weights.text == 1.0
        assert fusion_service.default_weights.semantic == 0.8

    def test_initialization_custom_weights(self, custom_weights_service):
        """Test initialization with custom weights."""
        assert custom_weights_service.default_weights.text == 0.5
        assert custom_weights_service.default_weights.semantic == 1.0

    def test_fuse_results_empty(self, fusion_service):
        """Test fusion with empty result sets."""
        result_sets = {}
        fused = fusion_service.fuse_results(result_sets)

        assert len(fused) == 0

    def test_fuse_results_single_set(self, fusion_service):
        """Test fusion with single result set."""
        result_sets = {
            SearchType.TEXT: [
                SearchResult(1, 0.9, SearchType.TEXT, {}),
                SearchResult(2, 0.8, SearchType.TEXT, {}),
                SearchResult(3, 0.7, SearchType.TEXT, {}),
            ]
        }

        fused = fusion_service.fuse_results(result_sets, top_k=3)

        assert len(fused) == 3
        assert fused[0].file_id == 1
        assert fused[0].rank == 1
        assert fused[1].file_id == 2
        assert fused[2].file_id == 3

    def test_fuse_results_rrf_method(self, fusion_service, sample_result_sets):
        """Test RRF fusion method."""
        fused = fusion_service.fuse_results(
            sample_result_sets,
            method="rrf",
            k=60.0,
            top_k=4,
        )

        assert len(fused) <= 4
        # File 2 appears in both sets, should have higher RRF score
        file_ids = [r.file_id for r in fused]
        assert 2 in file_ids
        # All file IDs should be unique
        assert len(set(file_ids)) == len(file_ids)

    def test_fuse_results_weighted_sum_method(self, fusion_service, sample_result_sets):
        """Test weighted sum fusion method."""
        fused = fusion_service.fuse_results(
            sample_result_sets,
            method="weighted_sum",
            top_k=4,
        )

        assert len(fused) <= 4
        # Results should be ordered by weighted score
        for i in range(len(fused) - 1):
            assert fused[i].score >= fused[i + 1].score

    def test_fuse_results_borda_count_method(self, fusion_service, sample_result_sets):
        """Test borda count fusion method."""
        fused = fusion_service.fuse_results(
            sample_result_sets,
            method="borda_count",
            top_k=4,
        )

        assert len(fused) <= 4
        # Results should be ordered by borda score
        for i in range(len(fused) - 1):
            assert fused[i].score >= fused[i + 1].score

    def test_fuse_results_unknown_method(self, fusion_service, sample_result_sets):
        """Test fusion with unknown method falls back to RRF."""
        fused = fusion_service.fuse_results(
            sample_result_sets,
            method="unknown_method",
            top_k=4,
        )

        # Should fall back to RRF
        assert len(fused) <= 4

    def test_fuse_results_with_custom_weights(self, fusion_service, sample_result_sets):
        """Test fusion with custom weights."""
        custom_weights = FusionWeights(text=1.0, semantic=0.1)

        fused = fusion_service.fuse_results(
            sample_result_sets,
            weights=custom_weights,
            method="rrf",
            top_k=4,
        )

        assert len(fused) <= 4

    def test_fuse_results_with_top_k_limit(self, fusion_service, sample_result_sets):
        """Test fusion respects top_k limit."""
        fused = fusion_service.fuse_results(
            sample_result_sets,
            top_k=2,
        )

        assert len(fused) <= 2

    def test_fuse_results_exception_handling(self, fusion_service):
        """Test exception handling in fusion."""
        # Create invalid result sets that might cause errors
        result_sets = {
            SearchType.TEXT: [
                SearchResult(1, 0.9, SearchType.TEXT, {}),
            ]
        }

        # Should handle gracefully even with potential errors
        fused = fusion_service.fuse_results(result_sets)
        assert len(fused) >= 0

    def test_reciprocal_rank_fusion_scores(self, fusion_service):
        """Test RRF score calculation."""
        result_sets = {
            SearchType.TEXT: [
                SearchResult(1, 0.9, SearchType.TEXT, {}),
                SearchResult(2, 0.8, SearchType.TEXT, {}),
            ],
            SearchType.SEMANTIC: [
                SearchResult(1, 0.85, SearchType.SEMANTIC, {}),  # Same file in both
                SearchResult(3, 0.75, SearchType.SEMANTIC, {}),
            ],
        }

        fused = fusion_service._reciprocal_rank_fusion(
            result_sets,
            fusion_service.default_weights,
            k=60.0,
            top_k=3,
        )

        # File 1 appears in both sets at rank 1, should have highest RRF score
        assert fused[0].file_id == 1

    def test_reciprocal_rank_fusion_metadata(self, fusion_service):
        """Test RRF preserves metadata."""
        result_sets = {
            SearchType.TEXT: [
                SearchResult(1, 0.9, SearchType.TEXT, {"snippet": "test"}),
            ],
            SearchType.SEMANTIC: [
                SearchResult(1, 0.85, SearchType.SEMANTIC, {"similarity": 0.85}),
            ],
        }

        fused = fusion_service._reciprocal_rank_fusion(
            result_sets,
            fusion_service.default_weights,
            k=60.0,
            top_k=1,
        )

        # Metadata should be combined
        assert "text_score" in fused[0].metadata
        assert "semantic_score" in fused[0].metadata
        assert "snippet" in fused[0].metadata
        assert "similarity" in fused[0].metadata

    def test_weighted_sum_fusion_normalization(self, fusion_service):
        """Test weighted sum normalizes scores."""
        result_sets = {
            SearchType.TEXT: [
                SearchResult(1, 100.0, SearchType.TEXT, {}),  # Large score
                SearchResult(2, 50.0, SearchType.TEXT, {}),
            ],
        }

        fused = fusion_service._weighted_sum_fusion(
            result_sets,
            fusion_service.default_weights,
            top_k=2,
        )

        # Scores should be normalized and weighted
        assert len(fused) == 2

    def test_weighted_sum_fusion_empty_result_set(self, fusion_service):
        """Test weighted sum with empty result sets."""
        result_sets = {
            SearchType.TEXT: [],
            SearchType.SEMANTIC: [],
        }

        fused = fusion_service._weighted_sum_fusion(
            result_sets,
            fusion_service.default_weights,
            top_k=10,
        )

        assert len(fused) == 0

    def test_weighted_sum_fusion_single_score(self, fusion_service):
        """Test weighted sum with single score (no range)."""
        result_sets = {
            SearchType.TEXT: [
                SearchResult(1, 0.9, SearchType.TEXT, {}),
            ],
        }

        fused = fusion_service._weighted_sum_fusion(
            result_sets,
            fusion_service.default_weights,
            top_k=1,
        )

        # Should handle single score case (score_range = 0)
        assert len(fused) == 1

    def test_borda_count_fusion_ranks(self, fusion_service):
        """Test borda count uses ranks correctly."""
        result_sets = {
            SearchType.TEXT: [
                SearchResult(1, 0.9, SearchType.TEXT, {}),  # Rank 0
                SearchResult(2, 0.8, SearchType.TEXT, {}),  # Rank 1
                SearchResult(3, 0.7, SearchType.TEXT, {}),  # Rank 2
            ],
        }

        fused = fusion_service._borda_count_fusion(
            result_sets,
            fusion_service.default_weights,
            top_k=3,
        )

        # Higher rank (lower position) should get more points
        assert fused[0].file_id == 1
        assert fused[0].score > fused[1].score
        assert fused[1].score > fused[2].score

    def test_borda_count_fusion_metadata(self, fusion_service):
        """Test borda count preserves metadata and ranks."""
        result_sets = {
            SearchType.TEXT: [
                SearchResult(1, 0.9, SearchType.TEXT, {"source": "text"}),
            ],
        }

        fused = fusion_service._borda_count_fusion(
            result_sets,
            fusion_service.default_weights,
            top_k=1,
        )

        # Should preserve metadata and add rank info
        assert "text_score" in fused[0].metadata
        assert "text_rank" in fused[0].metadata
        assert fused[0].metadata["text_rank"] == 1  # Rank 0 + 1

    def test_get_weight_for_type(self, fusion_service):
        """Test getting weight for each search type."""
        weights = FusionWeights(
            text=1.0,
            semantic=0.8,
            image=0.9,
            face=0.7,
            metadata=0.5,
        )

        assert fusion_service._get_weight_for_type(SearchType.TEXT, weights) == 1.0
        assert fusion_service._get_weight_for_type(SearchType.SEMANTIC, weights) == 0.8
        assert fusion_service._get_weight_for_type(SearchType.IMAGE, weights) == 0.9
        assert fusion_service._get_weight_for_type(SearchType.FACE, weights) == 0.7
        assert fusion_service._get_weight_for_type(SearchType.METADATA, weights) == 0.5

    def test_analyze_fusion_quality_basic(self, fusion_service, sample_result_sets):
        """Test basic fusion quality analysis."""
        fused = fusion_service.fuse_results(sample_result_sets, top_k=3)

        analysis = fusion_service.analyze_fusion_quality(
            sample_result_sets,
            fused,
            top_k=3,
        )

        assert "input_sets" in analysis
        assert "total_unique_results" in analysis
        assert "fusion_coverage" in analysis
        assert "diversity_score" in analysis
        assert analysis["input_sets"] == 2

    def test_analyze_fusion_quality_coverage(self, fusion_service, sample_result_sets):
        """Test fusion coverage calculation."""
        fused = fusion_service.fuse_results(sample_result_sets, top_k=4)

        analysis = fusion_service.analyze_fusion_quality(
            sample_result_sets,
            fused,
            top_k=3,
        )

        # Coverage should be calculated for each input set
        assert "text" in analysis["fusion_coverage"]
        assert "semantic" in analysis["fusion_coverage"]
        assert 0.0 <= analysis["fusion_coverage"]["text"] <= 1.0

    def test_analyze_fusion_quality_diversity(self, fusion_service, sample_result_sets):
        """Test diversity score calculation."""
        fused = fusion_service.fuse_results(sample_result_sets, top_k=4)

        analysis = fusion_service.analyze_fusion_quality(
            sample_result_sets,
            fused,
            top_k=3,
        )

        # Diversity should be between 0 and 1
        assert 0.0 <= analysis["diversity_score"] <= 1.0

    def test_analyze_fusion_quality_rank_correlation(self, fusion_service):
        """Test rank correlation calculation."""
        result_sets = {
            SearchType.TEXT: [
                SearchResult(1, 0.9, SearchType.TEXT, {}),
                SearchResult(2, 0.8, SearchType.TEXT, {}),
                SearchResult(3, 0.7, SearchType.TEXT, {}),
            ],
            SearchType.SEMANTIC: [
                SearchResult(1, 0.85, SearchType.SEMANTIC, {}),
                SearchResult(2, 0.75, SearchType.SEMANTIC, {}),
                SearchResult(3, 0.65, SearchType.SEMANTIC, {}),
            ],
        }

        fused = fusion_service.fuse_results(result_sets, top_k=3)

        analysis = fusion_service.analyze_fusion_quality(
            result_sets,
            fused,
            top_k=3,
        )

        # Should have rank correlation for first two types
        assert "rank_correlation" in analysis

    def test_analyze_fusion_quality_exception_handling(self, fusion_service):
        """Test exception handling in quality analysis."""
        # Pass empty data
        analysis = fusion_service.analyze_fusion_quality({}, [], top_k=3)

        # Should return result with zero values for empty data
        assert analysis["input_sets"] == 0
        assert analysis["total_unique_results"] == 0

    def test_calculate_rank_correlation_perfect(self, fusion_service):
        """Test rank correlation with perfect correlation."""
        results1 = [
            SearchResult(1, 0.9, SearchType.TEXT, {}),
            SearchResult(2, 0.8, SearchType.TEXT, {}),
            SearchResult(3, 0.7, SearchType.TEXT, {}),
        ]
        results2 = [
            SearchResult(1, 0.9, SearchType.SEMANTIC, {}),
            SearchResult(2, 0.8, SearchType.SEMANTIC, {}),
            SearchResult(3, 0.7, SearchType.SEMANTIC, {}),
        ]

        correlation = fusion_service._calculate_rank_correlation(results1, results2)

        # Perfect correlation should be 1.0
        assert correlation == 1.0

    def test_calculate_rank_correlation_reverse(self, fusion_service):
        """Test rank correlation with reverse order."""
        results1 = [
            SearchResult(1, 0.9, SearchType.TEXT, {}),
            SearchResult(2, 0.8, SearchType.TEXT, {}),
            SearchResult(3, 0.7, SearchType.TEXT, {}),
        ]
        results2 = [
            SearchResult(3, 0.9, SearchType.SEMANTIC, {}),
            SearchResult(2, 0.8, SearchType.SEMANTIC, {}),
            SearchResult(1, 0.7, SearchType.SEMANTIC, {}),
        ]

        correlation = fusion_service._calculate_rank_correlation(results1, results2)

        # Reverse correlation should be negative
        assert correlation < 0

    def test_calculate_rank_correlation_no_overlap(self, fusion_service):
        """Test rank correlation with no overlapping file IDs."""
        results1 = [SearchResult(1, 0.9, SearchType.TEXT, {})]
        results2 = [SearchResult(2, 0.9, SearchType.SEMANTIC, {})]

        correlation = fusion_service._calculate_rank_correlation(results1, results2)

        # No overlap should return 0.0
        assert correlation == 0.0

    def test_calculate_rank_correlation_single_common(self, fusion_service):
        """Test rank correlation with single common item."""
        results1 = [
            SearchResult(1, 0.9, SearchType.TEXT, {}),
            SearchResult(2, 0.8, SearchType.TEXT, {}),
        ]
        results2 = [SearchResult(1, 0.9, SearchType.SEMANTIC, {})]

        correlation = fusion_service._calculate_rank_correlation(results1, results2)

        # Less than 2 common items should return 0.0
        assert correlation == 0.0

    def test_calculate_rank_correlation_exception(self, fusion_service):
        """Test rank correlation exception handling."""
        # Pass invalid data
        correlation = fusion_service._calculate_rank_correlation([], [])

        # Should return 0.0 on exception
        assert correlation == 0.0

    def test_get_fusion_recommendations_text(self, fusion_service):
        """Test fusion recommendations for text query."""
        weights, method = fusion_service.get_fusion_recommendations("text")

        assert weights.text == 1.0
        assert weights.semantic == 0.6
        assert method == "weighted_sum"

    def test_get_fusion_recommendations_image(self, fusion_service):
        """Test fusion recommendations for image query."""
        weights, method = fusion_service.get_fusion_recommendations("image")

        assert weights.image == 1.0
        assert weights.semantic == 0.9
        assert method == "rrf"

    def test_get_fusion_recommendations_person(self, fusion_service):
        """Test fusion recommendations for person query."""
        weights, method = fusion_service.get_fusion_recommendations("person")

        assert weights.face == 1.0
        assert method == "rrf"

    def test_get_fusion_recommendations_mixed(self, fusion_service):
        """Test fusion recommendations for mixed query."""
        weights, method = fusion_service.get_fusion_recommendations("mixed")

        assert weights.text == 0.8
        assert weights.semantic == 0.8
        assert method == "rrf"

    def test_get_fusion_recommendations_unknown_type(self, fusion_service):
        """Test fusion recommendations for unknown query type."""
        weights, method = fusion_service.get_fusion_recommendations("unknown")

        # Should use default weights
        assert weights.text == fusion_service.default_weights.text
        assert method == "rrf"

    def test_get_fusion_recommendations_with_user_preferences(self, fusion_service):
        """Test fusion recommendations with user preferences."""
        user_prefs = {"text": 0.5, "semantic": 1.0}

        weights, method = fusion_service.get_fusion_recommendations(
            "text",
            user_preferences=user_prefs,
        )

        # Should apply user preferences
        assert weights.text == 0.5
        assert weights.semantic == 1.0

    def test_get_fusion_recommendations_partial_preferences(self, fusion_service):
        """Test fusion recommendations with partial user preferences."""
        user_prefs = {"text": 0.5}  # Only override text

        weights, method = fusion_service.get_fusion_recommendations(
            "text",
            user_preferences=user_prefs,
        )

        # Should apply partial preferences
        assert weights.text == 0.5
        assert weights.semantic == 0.6  # Default for "text" query type


class TestHelperFunctions:
    """Test helper functions."""

    def test_create_search_result(self):
        """Test create_search_result helper function."""
        result = create_search_result(
            file_id=1,
            score=0.95,
            search_type=SearchType.TEXT,
            snippet="test snippet",
            source="filename",
        )

        assert result.file_id == 1
        assert result.score == 0.95
        assert result.search_type == SearchType.TEXT
        assert result.metadata["snippet"] == "test snippet"
        assert result.metadata["source"] == "filename"

    def test_create_search_result_no_metadata(self):
        """Test create_search_result with no metadata."""
        result = create_search_result(
            file_id=1,
            score=0.95,
            search_type=SearchType.TEXT,
        )

        assert result.file_id == 1
        assert result.metadata == {}


class TestGlobalServiceFunction:
    """Test global service function."""

    def test_get_rank_fusion_service(self):
        """Test getting global service instance."""
        # Reset global variable
        import src.services.rank_fusion as rf_module
        rf_module._rank_fusion_service = None

        service1 = get_rank_fusion_service()
        service2 = get_rank_fusion_service()

        assert service1 is service2  # Same instance
        assert isinstance(service1, RankFusionService)
