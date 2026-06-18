import sys
import shutil
from pathlib import Path
from uuid import uuid4

import pytest


BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

LOCAL_TMP_ROOT = BACKEND_ROOT / ".pytest-tmp"
LOCAL_TMP_ROOT.mkdir(exist_ok=True)


@pytest.fixture
def tmp_path():
    path = LOCAL_TMP_ROOT / f"case-{uuid4().hex[:8]}"
    path.mkdir(parents=True, exist_ok=False)
    try:
        yield path
    finally:
        shutil.rmtree(path, ignore_errors=True)
