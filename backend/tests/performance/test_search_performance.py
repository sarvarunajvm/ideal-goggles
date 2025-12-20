"""Performance benchmarks for search services."""

import asyncio
import logging
import random
import statistics
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import numpy as np
import pytest

from src.services.text_search import TextSearchService
from src.services.vector_search import FAISSVectorSearchService

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)


class PerformanceBenchmark:
    """Base class for performance benchmarks."""

    def measure_time(self, func, *args, **kwargs):
        """Measure execution time of a function."""
        start_time = time.perf_counter()
        result = func(*args, **kwargs)
        end_time = time.perf_counter()
        return result, end_time - start_time

    async def measure_time_async(self, func, *args, **kwargs):
        """Measure execution time of an async function."""
        start_time = time.perf_counter()
        result = await func(*args, **kwargs)
        end_time = time.perf_counter()
        return result, end_time - start_time

    def run_multiple_iterations(self, func, iterations=10, *args, **kwargs):
        """Run function multiple times and collect timing statistics."""
        times = []
        results = []

        for _ in range(iterations):
            result, duration = self.measure_time(func, *args, **kwargs)
            times.append(duration)
            results.append(result)

        return {
            "times": times,
            "results": results,
            "mean": statistics.mean(times),
            "median": statistics.median(times),
            "stdev": statistics.stdev(times) if len(times) > 1 else 0,
            "min": min(times),
            "max": max(times),
            "p95": (
                sorted(times)[int(0.95 * len(times))]
                if len(times) >= 20
                else max(times)
            ),
            "p99": (
                sorted(times)[int(0.99 * len(times))]
                if len(times) >= 100
                else max(times)
            ),
        }


@pytest.mark.performance
class BenchmarkTextSearch(PerformanceBenchmark):
    """Performance tests for text search service."""

    def setup_method(self):
        """Set up test fixtures."""
        self.results = {}
        self.service = TextSearchService()

        # Create mock database with realistic data size
        self.mock_photos = self._generate_mock_photos(10000)

    def _generate_mock_photos(self, count: int) -> list[dict]:
        """Generate mock photo data for testing."""
        photos = []
        folders = [
            "/photos/2020",
            "/photos/2021",
            "/photos/2022",
            "/photos/2023",
            "/documents",
            "/scans",
        ]
        extensions = [".jpg", ".jpeg", ".png", ".tiff"]

        for i in range(count):
            folder = random.choice(folders)
            filename = f"photo_{i:06d}{random.choice(extensions)}"
            path = f"{folder}/{filename}"

            photos.append(
                {
                    "file_id": i + 1,
                    "path": path,
                    "filename": filename,
                    "folder": folder,
                    "score": random.uniform(0.1, 1.0),
                }
            )

        return photos

    def test_filename_search_performance(self):
        """Benchmark filename search performance."""
        # Test with different query lengths
        queries = [
            "photo",
            "photo_001",
            "specific_filename",
            "very_specific_long_filename_with_details",
        ]

        for query in queries:
            with self.service._get_database() as db:
                # Mock database response
                results = self.run_multiple_iterations(
                    self._mock_filename_search, iterations=100, query=query
                )

                self.results[f"filename_search_{len(query)}_chars"] = results

                # Performance assertions
                assert (
                    results["mean"] < 0.05
                ), f"Filename search too slow: {results['mean']:.3f}s"
                assert (
                    results["p95"] < 0.1
                ), f"95th percentile too slow: {results['p95']:.3f}s"

    def _mock_filename_search(self, query: str):
        """Mock filename search for performance testing."""
        # Simulate database query processing
        matching_photos = [
            photo
            for photo in self.mock_photos
            if query.lower() in photo["filename"].lower()
        ]
        return matching_photos[:50]  # Limit results

    def test_full_text_search_performance(self):
        """Benchmark full-text search performance."""
        queries = [
            "wedding",
            "birthday party",
            "family vacation photos",
            "corporate event documentation",
        ]

        for query in queries:
            results = self.run_multiple_iterations(
                self._mock_fts_search, iterations=50, query=query
            )

            self.results[f"fts_search_{len(query.split())}_words"] = results

            # Performance assertions
            assert results["mean"] < 0.2, f"FTS search too slow: {results['mean']:.3f}s"
            assert (
                results["p95"] < 0.5
            ), f"95th percentile too slow: {results['p95']:.3f}s"

    def _mock_fts_search(self, query: str):
        """Mock full-text search for performance testing."""
        # Simulate FTS processing
        time.sleep(random.uniform(0.01, 0.05))  # Simulate DB latency
        return [{"file_id": i, "score": random.uniform(0.3, 1.0)} for i in range(1, 21)]

    def test_combined_search_performance(self):
        """Benchmark combined search performance."""
        test_cases = [
            {"query": "photo", "from_date": None, "to_date": None, "folder": None},
            {
                "query": "wedding",
                "from_date": "2023-01-01",
                "to_date": "2023-12-31",
                "folder": None,
            },
            {
                "query": "document",
                "from_date": None,
                "to_date": None,
                "folder": "/documents",
            },
        ]

        for i, case in enumerate(test_cases):
            results = self.run_multiple_iterations(
                self._mock_combined_search, iterations=30, **case
            )

            self.results[f"combined_search_case_{i}"] = results

            # Performance assertions
            assert (
                results["mean"] < 0.5
            ), f"Combined search too slow: {results['mean']:.3f}s"
            assert (
                results["p95"] < 1.0
            ), f"95th percentile too slow: {results['p95']:.3f}s"

    def _mock_combined_search(
        self, query: str, from_date=None, to_date=None, folder=None
    ):
        """Mock combined search for performance testing."""
        # Simulate multiple database queries
        filename_results = self._mock_filename_search(query)
        fts_results = self._mock_fts_search(query)

        # Simulate result combination
        combined = {}
        for result in filename_results + fts_results:
            file_id = result.get("file_id", hash(result.get("filename", "")))
            if file_id not in combined:
                combined[file_id] = result

        return list(combined.values())

    def test_concurrent_search_performance(self):
        """Benchmark concurrent search performance."""
        queries = [f"query_{i}" for i in range(20)]

        start_time = time.perf_counter()

        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [
                executor.submit(self._mock_filename_search, query) for query in queries
            ]

            results = []
            for future in as_completed(futures):
                results.append(future.result())

        total_time = time.perf_counter() - start_time

        self.results["concurrent_search"] = {
            "total_time": total_time,
            "queries_per_second": len(queries) / total_time,
            "results_count": sum(len(r) for r in results),
        }

        # Performance assertions
        assert (
            self.results["concurrent_search"]["queries_per_second"] > 50
        ), "Concurrent search throughput too low"


@pytest.mark.performance
class BenchmarkVectorSearch(PerformanceBenchmark):
    """Performance tests for vector search service."""

    def setup_method(self):
        """Set up test fixtures."""
        self.results = {}
        import tempfile

        self.temp_dir = tempfile.mkdtemp()
        self.index_path = Path(self.temp_dir) / "benchmark_index.bin"

        self.service = FAISSVectorSearchService(index_path=str(self.index_path))

        # Generate test vectors
        self.test_vectors = self._generate_test_vectors()

    def _generate_test_vectors(self, count: int = 1000) -> list[np.ndarray]:
        """Generate test vectors for benchmarking."""
        np.random.seed(42)  # Reproducible results
        vectors = []

        for i in range(count):
            vector = np.random.rand(512).astype(np.float32)
            # Normalize for cosine similarity
            vector = vector / np.linalg.norm(vector)
            vectors.append(vector)

        return vectors

    def test_vector_addition_performance(self):
        """Benchmark vector addition performance."""
        vectors = self.test_vectors[:1000]

        # Test single additions
        results = self.run_multiple_iterations(
            self._add_single_vector, iterations=100, vectors=vectors[:100]
        )

        self.results = {}
        self.results["single_vector_addition"] = results

        # Performance assertions
        assert (
            results["mean"] < 0.01
        ), f"Vector addition too slow: {results['mean']:.4f}s"

    def _add_single_vector(self, vectors: list[np.ndarray]):
        """Add a single vector for performance testing."""
        vector = random.choice(vectors)
        file_id = random.randint(1, 10000)
        return self.service.add_vector(file_id, vector)

    def test_batch_vector_addition_performance(self):
        """Benchmark batch vector addition."""
        batch_sizes = [10, 50, 100, 500]

        for batch_size in batch_sizes:
            vectors = self.test_vectors[:batch_size]

            start_time = time.perf_counter()

            for i, vector in enumerate(vectors):
                self.service.add_vector(i + 1, vector)

            end_time = time.perf_counter()

            if not hasattr(self, "results"):
                self.results = {}
            self.results[f"batch_addition_{batch_size}"] = {
                "total_time": end_time - start_time,
                "vectors_per_second": batch_size / (end_time - start_time),
                "time_per_vector": (end_time - start_time) / batch_size,
            }

            # Performance assertions
            vectors_per_second = self.results[f"batch_addition_{batch_size}"][
                "vectors_per_second"
            ]
            assert (
                vectors_per_second > 100
            ), f"Batch addition too slow: {vectors_per_second:.1f} vectors/s"

    def test_similarity_search_performance(self):
        """Benchmark similarity search performance."""
        # Add test vectors to index
        for i, vector in enumerate(self.test_vectors[:1000]):
            self.service.add_vector(i + 1, vector)

        # Test different k values
        k_values = [1, 5, 10, 50, 100]
        query_vector = self.test_vectors[0]

        for k in k_values:
            results = self.run_multiple_iterations(
                self.service.search_similar,
                iterations=100,
                query_vector=query_vector,
                k=k,
            )

            if not hasattr(self, "results"):
                self.results = {}
            self.results[f"similarity_search_k{k}"] = results

            # Performance assertions
            assert (
                results["mean"] < 0.1
            ), f"Similarity search k={k} too slow: {results['mean']:.3f}s"

    def test_index_size_scaling(self):
        """Test performance scaling with index size."""
        index_sizes = [100, 500, 1000, 5000, 10000]
        query_vector = self.test_vectors[0]

        for size in index_sizes:
            # Build index of specific size
            service = FAISSVectorSearchService()

            # Add vectors
            start_build = time.perf_counter()
            for i in range(size):
                vector = self.test_vectors[i % len(self.test_vectors)]
                service.add_vector(i + 1, vector)
            build_time = time.perf_counter() - start_build

            # Test search performance
            search_times = []
            for _ in range(20):
                start_search = time.perf_counter()
                service.search_similar(query_vector, k=10)
                search_times.append(time.perf_counter() - start_search)

            if not hasattr(self, "results"):
                self.results = {}
            self.results[f"scaling_{size}"] = {
                "index_size": size,
                "build_time": build_time,
                "mean_search_time": statistics.mean(search_times),
                "median_search_time": statistics.median(search_times),
                "max_search_time": max(search_times),
            }

            # Performance should not degrade significantly with size
            mean_search_time = statistics.mean(search_times)
            assert (
                mean_search_time < 0.2
            ), f"Search time degraded with size {size}: {mean_search_time:.3f}s"

    def test_concurrent_search_performance(self):
        """Benchmark concurrent similarity search."""
        # Add test vectors
        for i, vector in enumerate(self.test_vectors[:1000]):
            self.service.add_vector(i + 1, vector)

        query_vectors = self.test_vectors[:50]

        start_time = time.perf_counter()

        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [
                executor.submit(self.service.search_similar, vector, 10)
                for vector in query_vectors
            ]

            results = []
            for future in as_completed(futures):
                results.append(future.result())

        total_time = time.perf_counter() - start_time

        if not hasattr(self, "results"):
            self.results = {}
        self.results["concurrent_vector_search"] = {
            "total_time": total_time,
            "searches_per_second": len(query_vectors) / total_time,
            "results_count": sum(len(r) for r in results),
        }

        # Performance assertions
        searches_per_second = self.results["concurrent_vector_search"][
            "searches_per_second"
        ]
        assert (
            searches_per_second > 10
        ), f"Concurrent search throughput too low: {searches_per_second:.1f}/s"

    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)


def run_performance_benchmarks():
    """Run all performance benchmarks and generate report."""
    benchmark_classes = [
        BenchmarkTextSearch,
        BenchmarkVectorSearch,
    ]

    all_results = {}

    for benchmark_class in benchmark_classes:
        logger.info(f"\nRunning {benchmark_class.__name__}...")
        benchmark = benchmark_class()

        # Run setup
        benchmark.setup_method()

        # Run all test methods
        for method_name in dir(benchmark):
            if method_name.startswith("test_"):
                logger.info(f"  Running {method_name}...")
                try:
                    method = getattr(benchmark, method_name)
                    method()
                except Exception as e:
                    logger.exception(f"    Failed: {e}")

        # Collect results
        if hasattr(benchmark, "results"):
            all_results[benchmark_class.__name__] = benchmark.results

        # Run teardown if exists
        if hasattr(benchmark, "teardown_method"):
            benchmark.teardown_method()

    # Generate performance report
    _generate_performance_report(all_results)

    return all_results


def _generate_performance_report(results: dict):
    """Generate a performance benchmark report."""
    report_path = Path("performance_report.txt")

    with open(report_path, "w") as f:
        f.write("PHOTO SEARCH PERFORMANCE BENCHMARK REPORT\n")
        f.write("=" * 50 + "\n\n")

        for class_name, class_results in results.items():
            f.write(f"{class_name}\n")
            f.write("-" * len(class_name) + "\n")

            for test_name, test_results in class_results.items():
                f.write(f"  {test_name}:\n")

                if isinstance(test_results, dict) and "mean" in test_results:
                    f.write(f"    Mean: {test_results['mean']:.4f}s\n")
                    f.write(f"    Median: {test_results['median']:.4f}s\n")
                    f.write(
                        f"    95th percentile: {test_results.get('p95', 'N/A'):.4f}s\n"
                    )
                    f.write(f"    Min: {test_results['min']:.4f}s\n")
                    f.write(f"    Max: {test_results['max']:.4f}s\n")
                else:
                    f.write(f"    Result: {test_results}\n")

                f.write("\n")

            f.write("\n")

    logger.info(f"Performance report generated: {report_path}")


if __name__ == "__main__":
    run_performance_benchmarks()
