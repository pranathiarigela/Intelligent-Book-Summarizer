# tests/conftest.py
import sys
from pathlib import Path

# Ensure project root is on sys.path so `import utils.database` works reliably.
# This adds the parent directory of tests/ (the project root).
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Now safe to import project modules
from utils.database import init_db, connect_db
import pytest

@pytest.fixture
def db_conn(tmp_path):
    """
    Creates a fresh test DB with tables before each test.
    Returns an active sqlite3.Connection object.
    """
    db_path = tmp_path / "test_app.db"
    init_db(str(db_path))
    conn = connect_db(str(db_path))
    yield conn
    conn.close()
