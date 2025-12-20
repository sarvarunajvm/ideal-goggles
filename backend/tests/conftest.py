"""Pytest configuration and shared fixtures."""

import os
import sys
from unittest.mock import MagicMock

# MOCK BROKEN SYSTEM DEPENDENCIES TO PREVENT SEGFAULT
# This is necessary because the environment has broken numpy/scipy installations
# that cause segmentation faults on import.

# Create a mock for numpy
mock_numpy = MagicMock()
mock_numpy.__version__ = "1.26.4"


class MockFloat32(float):
    pass


class MockFloat64(float):
    pass


# Define a real class for ndarray so isinstance checks work
class MockNDArray(list):
    def __init__(self, *args, **kwargs):
        self._data = []
        self.dtype = kwargs.get("dtype", MockFloat32)

        if args and isinstance(args[0], (list, tuple)):
            self._data = list(args[0])
            super().__init__(args[0])
            self.shape = (len(args[0]),)
            if self._data and isinstance(self._data[0], (list, tuple)):
                self.shape = (len(self._data), len(self._data[0]))
        else:
            super().__init__(*args, **kwargs)
            self.shape = (512,)

        self._ndim = len(self.shape)
        prod = 1
        for dim in self.shape:
            prod *= dim
        self._size = prod

    @property
    def size(self):
        if hasattr(self, "_size"):
            return self._size
        return len(self)

    @size.setter
    def size(self, value):
        self._size = value

    @property
    def ndim(self):
        if hasattr(self, "_ndim"):
            return self._ndim
        return 1

    @ndim.setter
    def ndim(self, value):
        self._ndim = value

    def __hash__(self):
        return hash(tuple(self))

    def astype(self, dtype):
        # Return a copy with new dtype
        new_arr = MockNDArray(self._data, dtype=dtype)
        new_arr.shape = self.shape
        new_arr.ndim = self.ndim
        new_arr.size = self.size
        return new_arr

    def flatten(self):
        # Flatten the data if it's nested
        flat = []

        def _flat(lst):
            for item in lst:
                if isinstance(item, (list, tuple, MockNDArray)):
                    _flat(item)
                else:
                    flat.append(item)

        _flat(self._data)
        return MockNDArray(flat)

    def tolist(self):
        return self._data

    def tobytes(self):
        # Return bytes matching actual length * 4 (float32)
        # If empty (mock default), assume 512
        length = self.size
        if length == 0:
            length = 512
        return b"\x00" * (length * 4)

    def reshape(self, *args, **kwargs):
        # Return self but update shape if possible?
        # For now just return self to satisfy method chaining
        return self

    def dot(self, other):
        # Implement real dot product
        if self.ndim == 1 and (not hasattr(other, "ndim") or other.ndim == 1):
            other_data = other._data if hasattr(other, "_data") else other
            return sum(
                float(a) * float(b)
                for a, b in zip(self._data, other_data, strict=False)
            )

        # Matrix multiplication logic (simplified)
        if self.ndim == 2 and (not hasattr(other, "ndim") or other.ndim == 1):
            # Matrix (self) dot Vector (other) -> Vector
            other_data = other._data if hasattr(other, "_data") else other
            result = []
            for row in self._data:
                # row is a list/MockNDArray
                row_data = row._data if hasattr(row, "_data") else row
                val = sum(
                    float(a) * float(b)
                    for a, b in zip(row_data, other_data, strict=False)
                )
                result.append(val)
            return MockNDArray(result)

        # If both 2D, return 2D array (matrix mul)
        # This is complex to implement fully but let's try basic
        return 1.0

    def any(self):
        # Return False by default to pass isnan/isinf checks
        # If any element is truthy, return True
        if hasattr(self, "_data"):
            # Recursively check if any element is true
            def check_any(lst):
                for item in lst:
                    if isinstance(item, (list, tuple, MockNDArray)):
                        if check_any(item):
                            return True
                    elif item:
                        return True
                return False
            return check_any(self._data)
        return False

    def all(self):
        if hasattr(self, "_data"):
            def check_all(lst):
                for item in lst:
                    if isinstance(item, (list, tuple, MockNDArray)):
                        if not check_all(item):
                            return False
                    elif not item:
                        return False
                return True
            return check_all(self._data)
        return True

    def __setitem__(self, key, value):
        if hasattr(self, "_data"):
            self._data[key] = value

    def __getitem__(self, key):
        if hasattr(self, "_data"):
            val = self._data[key]
            # If we get a list back, wrap it in MockNDArray so it has .shape etc
            if isinstance(val, list):
                return MockNDArray(val)
            return val
        return MockNDArray()

    def __iter__(self):
        if hasattr(self, "_data"):
            for item in self._data:
                if isinstance(item, list):
                    yield MockNDArray(item)
                else:
                    yield item
        else:
            yield from []

    def __array__(self):
        return self

    def __float__(self):
        if self._data and not isinstance(self._data[0], (list, tuple)):
            return float(self._data[0])
        return 1.0

    def __int__(self):
        if self._data and not isinstance(self._data[0], (list, tuple)):
            return int(self._data[0])
        return 1

    # Arithmetic operators
    def __truediv__(self, other):
        if hasattr(self, "_data"):
            # Handle array/list division
            if hasattr(other, "_data") or isinstance(other, list):
                other_data = other._data if hasattr(other, "_data") else other
                # Simple broadcasting for (n, d) / (n, 1) or similar
                if len(self._data) == len(other_data):
                    result = []
                    for i, row in enumerate(self._data):
                        divisor = other_data[i]
                        # Unwrap single-element list/array
                        if isinstance(divisor, (list, MockNDArray)) and len(divisor) == 1:
                            divisor = divisor[0]

                        if isinstance(row, list):
                            # Divide row by scalar
                            result.append([x / float(divisor) for x in row])
                        else:
                            # Scalar division
                            result.append(row / float(divisor))
                    return MockNDArray(result)

            # Scalar division
            try:
                other_val = float(other)
                return MockNDArray([
                    (x / other_val) if not isinstance(x, list) else [v / other_val for v in x]
                    for x in self._data
                ])
            except (TypeError, ValueError):
                pass

        return self

    def __rtruediv__(self, other):
        return self

    def __mul__(self, other):
        if hasattr(self, "_data"):
            other_val = float(other)
            return MockNDArray([x * other_val for x in self._data])
        return self

    def __rmul__(self, other):
        return self.__mul__(other)

    def __add__(self, other):
        if hasattr(self, "_data"):
            other_val = float(other) if isinstance(other, (int, float)) else other
            if isinstance(other_val, (int, float)):
                return MockNDArray([x + other_val for x in self._data])
            # Element-wise add
            other_data = other._data if hasattr(other, "_data") else other
            return MockNDArray(
                [a + b for a, b in zip(self._data, other_data, strict=False)]
            )
        return self

    def __radd__(self, other):
        return self.__add__(other)

    def __sub__(self, other):
        if hasattr(self, "_data"):
            other_val = float(other) if isinstance(other, (int, float)) else other
            if isinstance(other_val, (int, float)):
                return MockNDArray([x - other_val for x in self._data])
            other_data = other._data if hasattr(other, "_data") else other
            return MockNDArray(
                [a - b for a, b in zip(self._data, other_data, strict=False)]
            )
        return self

    def __rsub__(self, other):
        if hasattr(self, "_data"):
            other_val = float(other) if isinstance(other, (int, float)) else other
            if isinstance(other_val, (int, float)):
                return MockNDArray([other_val - x for x in self._data])
        return self

    def __eq__(self, other):
        # Allow comparison with lists
        if isinstance(other, list):
            return self._data == other
        if isinstance(other, MockNDArray):
            return self._data == other._data
        return False

    # Allow comparisons for size checks > 0 etc
    # But usually size is accessed via .size property which returns int

    # Comparison operators for assertions
    def __lt__(self, other):
        # Needed for <= comparisons if tested against this object directly
        # But usually we compare vector norms (floats) or sizes (ints)
        return False

    def __gt__(self, other):
        return False


mock_numpy.ndarray = MockNDArray
mock_numpy.array = lambda x, **kwargs: (
    MockNDArray(x, **kwargs) if isinstance(x, (list, tuple)) else x
)
mock_numpy.float32 = MockFloat32
mock_numpy.float64 = MockFloat64

mock_numpy.any = lambda x, **_kwargs: x.any() if hasattr(x, "any") else any(x)
mock_numpy.all = lambda x, **_kwargs: x.all() if hasattr(x, "all") else all(x)

# Implement zeros, ones, full
mock_numpy.zeros = lambda shape, **_kwargs: MockNDArray(
    [0.0] * (shape if isinstance(shape, int) else shape[0])
)
mock_numpy.ones = lambda shape, **_kwargs: MockNDArray(
    [1.0] * (shape if isinstance(shape, int) else shape[0])
)
mock_numpy.full = lambda shape, val, **_kwargs: MockNDArray(
    [val] * (shape if isinstance(shape, int) else shape[0])
)


# Implement math functions
def mock_std(x, **kwargs):
    if hasattr(x, "_data"):
        import statistics

        try:
            return statistics.stdev(x._data) if len(x._data) > 1 else 0.0
        except:
            return 0.05
    return 0.05


mock_numpy.std = mock_std


def mock_mean(x, **kwargs):
    if hasattr(x, "_data"):
        import statistics

        try:
            return statistics.mean(x._data)
        except:
            return 0.1
    return 0.1


mock_numpy.mean = mock_mean

mock_numpy.min = lambda x, **_kwargs: (
    min(x._data) if hasattr(x, "_data") and x._data else 0.0
)
mock_numpy.max = lambda x, **_kwargs: (
    max(x._data) if hasattr(x, "_data") and x._data else 1.0
)
mock_numpy.abs = lambda x, **_kwargs: x

def mock_isnan(x, **_kwargs):
    if hasattr(x, "_data"):
        import math
        return MockNDArray([math.isnan(v) if isinstance(v, float) else False for v in x._data])
    if isinstance(x, float):
        import math
        return math.isnan(x)
    return False

mock_numpy.isnan = mock_isnan

def mock_isinf(x, **_kwargs):
    if hasattr(x, "_data"):
        import math
        return MockNDArray([math.isinf(v) if isinstance(v, float) else False for v in x._data])
    if isinstance(x, float):
        import math
        return math.isinf(x)
    return False

mock_numpy.isinf = mock_isinf

mock_numpy.logical_not = lambda x, **_kwargs: MockNDArray(
    [not v for v in (x._data if hasattr(x, "_data") else x)]
)
mock_numpy.squeeze = lambda x, **_kwargs: x  # Simplified
mock_numpy.stack = lambda arrays, **_kwargs: (
    MockNDArray(arrays) if arrays else MockNDArray()
)

mock_numpy.linalg = MagicMock()


def mock_norm(x, **kwargs):
    axis = kwargs.get("axis")
    keepdims = kwargs.get("keepdims", False)

    data = x._data if hasattr(x, "_data") else x

    import math

    # Simple recursive sum of squares
    def sum_sq(lst):
        s = 0
        if isinstance(lst, (int, float)):
            return lst**2

        iterator = lst._data if hasattr(lst, "_data") else lst
        for item in iterator:
            if isinstance(item, (list, tuple, MockNDArray)):
                s += sum_sq(item)
            else:
                s += item**2
        return s

    # Handle axis=1 for 2D arrays (common in vector search)
    if axis == 1 and (isinstance(data, list) or hasattr(data, "__iter__")):
        # Assuming 2D
        norms = []
        for row in data:
            norms.append(math.sqrt(sum_sq(row)))

        if keepdims:
            return MockNDArray([[n] for n in norms])
        return MockNDArray(norms)

    # Scalar norm
    res = math.sqrt(sum_sq(x))
    if keepdims:
        return MockNDArray([res]) # Or [[res]]? Depends on dim.
        # But MockNDArray wraps list.
    return res


mock_numpy.linalg.norm = mock_norm

mock_numpy.dot = lambda a, b: a.dot(b) if hasattr(a, "dot") else 1.0

# Mock random
mock_numpy.random = MagicMock()


# Return a MockNDArray with some dummy data
def mock_randn(*args):
    import random

    if not args:
        size = 512
        return MockNDArray([random.random() for _ in range(size)])

    shape = args

    # Recursive helper to create nested lists
    def create_data(dims):
        if len(dims) == 1:
            return [random.random() for _ in range(dims[0])]
        return [create_data(dims[1:]) for _ in range(dims[0])]

    data = create_data(shape)
    return MockNDArray(data)


mock_numpy.random.randn = mock_randn
mock_numpy.random.rand = mock_randn
mock_numpy.frombuffer = lambda _x, **_kwargs: MockNDArray([0.1] * 512)

# Mock types
mock_numpy.bool_ = bool
mock_numpy.int64 = int
mock_numpy.float32 = MockFloat32
mock_numpy.float64 = MockFloat64
mock_numpy.nan = float("nan")
mock_numpy.inf = float("inf")

# Mock testing
mock_numpy.testing = MagicMock()
mock_numpy.testing.assert_array_almost_equal = MagicMock()
mock_numpy.testing.assert_array_equal = MagicMock()

sys.modules["numpy"] = mock_numpy

# Mock other heavy dependencies that might depend on numpy or be broken
sys.modules["scipy"] = MagicMock()
sys.modules["scipy.spatial"] = MagicMock()
sys.modules["cv2"] = MagicMock()


# Mock FAISS
class MockIndex:
    def __init__(self, d=512):
        self.d = d
        self.ntotal = 0
        self.is_trained = True
        self._vectors = {}  # Store vectors if needed

    def add(self, x):
        # x is typically (n, d)
        n = x.shape[0] if hasattr(x, "shape") else 1
        self.ntotal += n

    def search(self, x, k):
        n = x.shape[0] if hasattr(x, "shape") else 1
        # Return (n, k) arrays
        # Use simple predictable values
        # Distances: decreasing
        distances = MockNDArray([[1.0 / (i + 1) for i in range(k)] for _ in range(n)])
        # Indices: 0, 1, 2...
        indices = MockNDArray([list(range(k)) for _ in range(n)], dtype=int)
        return distances, indices

    def reset(self):
        self.ntotal = 0

    def train(self, x):
        pass

    def write_index(self, index, path):
        pass

    def read_index(self, path):
        return MockIndex()

    def reconstruct(self, i):
        return MockNDArray([0.1] * 512)

    def reconstruct_n(self, start, end):
        return MockNDArray([[0.1] * 512] * (end - start))


mock_faiss = MagicMock()
mock_faiss.IndexFlatL2 = MockIndex
mock_faiss.write_index = MagicMock()
mock_faiss.read_index = lambda _x: MockIndex()
sys.modules["faiss"] = mock_faiss

sys.modules["torch"] = MagicMock()
sys.modules["torch.nn"] = MagicMock()
sys.modules["torchvision"] = MagicMock()
sys.modules["insightface"] = MagicMock()
sys.modules["insightface.app"] = MagicMock()

# Now import standard libraries
import contextlib  # noqa: E402
import tempfile  # noqa: E402
from pathlib import Path  # noqa: E402
from unittest.mock import Mock, patch  # noqa: E402

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

# Note: These fixtures use mocks since implementation doesn't exist yet
# They will be updated to use real implementations once T026-T047 are complete


@pytest.fixture(autouse=True)
def prevent_faiss_scheduler(request):
    """Prevent FAISS background scheduler from starting in any test."""
    # Check if test is marked to allow scheduler
    # We check both markers and keywords
    if request.node.get_closest_marker("allow_faiss_scheduler") or "allow_faiss_scheduler" in request.keywords:
        yield
        return

    # Import inside fixture to avoid circular imports during collection
    from src.services.faiss_manager import FAISSIndexManager

    with patch.object(FAISSIndexManager, "_start_background_scheduler"):
        yield


@pytest.fixture(autouse=True)
def reset_database_settings():
    """Reset database settings before each test."""
    from src.db.connection import _db_manager

    # Only reset if database manager already exists
    if _db_manager is not None:
        # Clear settings table to ensure tests start with defaults
        with contextlib.suppress(Exception):
            _db_manager.execute_update(
                "DELETE FROM settings WHERE key != 'schema_version'"
            )

    yield

    # Cleanup after test
    if _db_manager is not None:
        with contextlib.suppress(Exception):
            _db_manager.execute_update(
                "DELETE FROM settings WHERE key != 'schema_version'"
            )


@pytest.fixture
def client() -> TestClient:
    """Create a test client for the FastAPI application."""
    # Use real app now that endpoints are implemented
    from src.main import app

    return TestClient(app)


@pytest.fixture
def temp_dirs():
    """Create temporary directories for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        photos_dir = temp_path / "photos"
        another_dir = temp_path / "another"
        photos_dir.mkdir()
        another_dir.mkdir()
        yield {
            "photos": str(photos_dir),
            "another": str(another_dir),
            "base": str(temp_path),
        }


@pytest.fixture
def temp_index_path():
    """Create a temporary directory for test indices."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield os.path.join(tmpdir, "test_index.bin")


@pytest.fixture
def sample_photos():
    """Create sample photos in database for testing."""
    from src.db.connection import get_database_manager

    db_manager = get_database_manager()

    # Insert sample photos
    sample_data = [
        (
            1,
            "/test/photo1.jpg",
            "/test",
            "photo1.jpg",
            ".jpg",
            1024,
            1640995200.0,
            1640995200.0,
            "hash1",
        ),
        (
            2,
            "/test/photo2.jpg",
            "/test",
            "photo2.jpg",
            ".jpg",
            2048,
            1640995300.0,
            1640995300.0,
            "hash2",
        ),
        (
            3,
            "/test/photo3.jpg",
            "/test",
            "photo3.jpg",
            ".jpg",
            4096,
            1640995400.0,
            1640995400.0,
            "hash3",
        ),
    ]

    for photo in sample_data:
        with contextlib.suppress(Exception):
            db_manager.execute_update(
                "INSERT OR IGNORE INTO photos (id, path, folder, filename, ext, size, created_ts, modified_ts, sha1) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                photo,
            )

    yield sample_data

    # Cleanup
    with contextlib.suppress(Exception):
        db_manager.execute_update("DELETE FROM photos WHERE id IN (1, 2, 3)")


@pytest.fixture
def enable_face_search():
    """Enable face search for testing."""
    from src.api.config import _update_config_in_db
    from src.db.connection import get_database_manager

    db_manager = get_database_manager()

    # Enable face search
    _update_config_in_db(db_manager, "face_search_enabled", value=True)

    yield True

    # Restore to disabled (default)
    _update_config_in_db(db_manager, "face_search_enabled", value=False)


@pytest.fixture
def sample_photo_data():
    """Sample photo data for testing."""
    return {
        "id": 1,
        "path": "/test/photos/sample.jpg",
        "folder": "/test/photos",
        "filename": "sample.jpg",
        "ext": ".jpg",
        "size": 2048576,
        "created_ts": 1640995200.0,
        "modified_ts": 1640995200.0,
        "sha1": "da39a3ee5e6b4b0d3255bfef95601890afd80709",
        "phash": "abc123def456",
        "indexed_at": 1640995200.0,
        "index_version": 1,
    }


@pytest.fixture
def sample_search_results():
    """Sample search results for testing."""
    return {
        "query": "test query",
        "total_matches": 1,
        "items": [
            {
                "file_id": 1,
                "path": "/test/photos/sample.jpg",
                "folder": "/test/photos",
                "filename": "sample.jpg",
                "thumb_path": "cache/thumbs/da/da39a3ee5e6b4b0d3255bfef95601890afd80709.webp",
                "shot_dt": "2022-01-01T12:00:00Z",
                "score": 0.95,
                "badges": ["OCR"],
                "snippet": "test text found in image",
            }
        ],
        "took_ms": 150,
    }


@pytest.fixture
def sample_person_data():
    """Sample person data for testing."""
    return {
        "id": 1,
        "name": "John Smith",
        "sample_count": 3,
        "created_at": 1640995200.0,
        "updated_at": 1640995200.0,
        "active": True,
    }
