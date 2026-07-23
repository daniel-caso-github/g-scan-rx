import os

import pytest

# Ensure a DATABASE_URL exists for offline test runs. DATABASE_URL is required
# (no insecure default in src/config.py); in Docker it comes from app.env, but
# outside Docker we inject a throwaway URL so importing src.config never fails.
# Tests are offline-first and never open a real connection.
os.environ.setdefault(
    "DATABASE_URL", "postgresql+psycopg://test:test@localhost:5432/test"
)

from src.data.synthetic.catalog_seed import get_seed_catalog
from src.data.synthetic.generator import PrescriptionGenerator
from src.domain.value_objects.image_crop import ImageCrop


@pytest.fixture(scope="session")
def catalog():
    return get_seed_catalog()


@pytest.fixture(scope="session")
def generator(catalog):
    return PrescriptionGenerator(catalog=catalog, seed=42)


@pytest.fixture
def crop_dummy():
    return ImageCrop(bbox=(0, 0, 100, 30), crop_ref="dummy.png")
