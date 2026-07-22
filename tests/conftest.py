import pytest

from src.data.synthetic.catalog_seed import get_seed_catalog
from src.data.synthetic.generator import RecetaGenerator
from src.domain.value_objects.recorte_imagen import RecorteImagen


@pytest.fixture(scope="session")
def catalog():
    return get_seed_catalog()


@pytest.fixture(scope="session")
def generator(catalog):
    return RecetaGenerator(catalog=catalog, seed=42)


@pytest.fixture
def recorte_dummy():
    return RecorteImagen(bbox=(0, 0, 100, 30), crop_ref="dummy.png")
