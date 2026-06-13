"""
pytest configuration for synesthetic-familiar.

Adds the project root (projects/synesthetic-familiar/) to sys.path so that
`from host.familiar_protocol import ...` resolves correctly when pytest is
invoked from any working directory.

Also adds the tests/ directory so test modules can do `from helpers import ...`
to access shared test infrastructure (FakeTransport, FakeClock, etc.).
"""
import sys
import pathlib

# Insert the project root (the directory containing `host/`) at the front of sys.path
_PROJECT_ROOT = pathlib.Path(__file__).parent.resolve()
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

# Insert tests/ so `from helpers import ...` works in test files
_TESTS_DIR = _PROJECT_ROOT / "tests"
if str(_TESTS_DIR) not in sys.path:
    sys.path.insert(0, str(_TESTS_DIR))
