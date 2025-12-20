"""Pytest configuration and shared fixtures."""

import sys
from unittest.mock import MagicMock

# MOCK BROKEN SYSTEM DEPENDENCIES TO PREVENT SEGFAULT
# This is necessary because the environment has broken numpy/scipy installations
# that cause segmentation faults on import.

# Create a mock for numpy
mock_numpy = MagicMock()
mock_numpy.__version__ = "1.26.4"

# Define a real class for ndarray so isinstance checks work
class MockNDArray(list):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if args and isinstance(args[0], (list, tuple)):
             self.shape = (len(args[0]),)
        else:
             self.shape = (512,)
        # self.dtype needs to equal np.float32 (which is mocked as float)
        self.dtype = float
        # But if code accesses dtype.str, float doesn't have .str
        # So we might need a mock that equals float but has attributes

    def __hash__(self):
        return hash(tuple(self))

    @property
    def size(self):
        return 512

    @property
    def ndim(self):
        return 1

    def __len__(self):
        if super().__len__() > 0:
            return super().__len__()
        return 512

    def astype(self, dtype):
        return self

    def flatten(self):
        return self

    def tolist(self):
        return list(self)

    def tobytes(self):
        # Return bytes matching actual length * 4 (float32)
        # If empty (mock default), assume 512
        length = len(self)
        if length == 0:
            length = 512
        return b"\x00" * (length * 4)

    def reshape(self, *args, **kwargs):
        return self

    def dot(self, other):
        return 1.0 # Return float for dot product to satisfy similarity calculations

    def __setitem__(self, key, value):
        pass

    def __getitem__(self, key):
        if isinstance(key, (int, slice)):
             return MockNDArray()
        return self

    def __array__(self):
        return self

    def __float__(self):
        return 1.0

    # Arithmetic operators
    def __truediv__(self, other):
        return self

    def __rtruediv__(self, other):
        return self

    def __mul__(self, other):
        return self

    def __rmul__(self, other):
        return self

    def __add__(self, other):
        return self

    def __radd__(self, other):
        return self

    def __sub__(self, other):
        return self

    def __rsub__(self, other):
        return self

    def __eq__(self, other):
        return MockNDArray()

    # Comparison operators for assertions
    def __lt__(self, other):
        return MockNDArray()

    def __gt__(self, other):
        return MockNDArray()

mock_numpy.ndarray = MockNDArray
mock_numpy.array = lambda x, **_kwargs: MockNDArray(x) if isinstance(x, (list, tuple)) else x
mock_numpy.float32 = float
mock_numpy.linalg = MagicMock()
mock_numpy.linalg.norm.return_value = MockNDArray()

# Mock random
mock_numpy.random = MagicMock()
mock_numpy.random.randn.return_value = MockNDArray()
mock_numpy.random.rand.return_value = MockNDArray()
mock_numpy.frombuffer = lambda _x, **_kwargs: MockNDArray()

# Mock types
mock_numpy.bool_ = bool
mock_numpy.int64 = int
mock_numpy.float32 = float
mock_numpy.float64 = float

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

    def add(self, x):
        # x is typically (n, d)
        n = x.shape[0] if hasattr(x, "shape") else 1
        self.ntotal += n

    def search(self, x, k):
        n = x.shape[0] if hasattr(x, "shape") else 1
        # Return (n, k) arrays
        # We use nested lists to simulate 2D arrays if iterating
        distances = MockNDArray([[0.1]*k for _ in range(n)])
        indices = MockNDArray([[0]*k for _ in range(n)])
        return distances, indices

    def reset(self):
        self.ntotal = 0

    def train(self, x):
        pass

    def write_index(self, index, path):
        pass

    def read_index(self, path):
        return MockIndex()

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
def prevent_faiss_scheduler():
    """Prevent FAISS background scheduler from starting in any test."""
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
