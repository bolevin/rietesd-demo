from __future__ import annotations

import os
from pathlib import Path

import pytest

# the window tests need no screen; must be set before Qt is imported
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from rietesd_demo.adapters.topas import TopasReader
from rietesd_demo.domain import Pattern
from rietesd_demo.main import data_path


@pytest.fixture(scope="session")
def sample_path() -> Path:
    return data_path("sample_pattern.txt")


@pytest.fixture(scope="session")
def sample(sample_path: Path) -> Pattern:
    return TopasReader().read(sample_path)


@pytest.fixture
def tiny() -> Pattern:
    """Four points small enough to check every sum by hand."""
    return Pattern(
        two_theta=(10.0, 10.1, 10.2, 10.3),
        y_obs=(100.0, 400.0, 100.0, 25.0),
        y_calc=(90.0, 420.0, 110.0, 20.0),
        background=(20.0, 20.0, 20.0, 20.0),
    )
