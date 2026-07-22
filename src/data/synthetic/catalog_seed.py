"""Small seed catalog for development and tests.

Real drug names and presentations; dose ranges are approximate for
illustration only (not medical advice). For development and offline
evaluation only.
"""

from src.domain.entities.catalog_item import CatalogItem
from src.domain.services.make_id import make_id

_SEED_DATA = [
    {
        "active_ingredient": "amoxicilina",
        "brand_name": "Amoxil",
        "presentation": "cápsula 500 mg",
        "concentration": "500 mg",
        "form": "capsula",
        "dose_range": {"min": 250, "max": 1000, "unit": "mg"},
        "source": "cima",
        "country": "ES",
    },
    {
        "active_ingredient": "ibuprofeno",
        "brand_name": "Nurofen",
        "presentation": "comprimido 400 mg",
        "concentration": "400 mg",
        "form": "comprimido",
        "dose_range": {"min": 200, "max": 800, "unit": "mg"},
        "source": "cima",
        "country": "ES",
    },
    {
        "active_ingredient": "paracetamol",
        "brand_name": "Panadol",
        "presentation": "comprimido 500 mg",
        "concentration": "500 mg",
        "form": "comprimido",
        "dose_range": {"min": 325, "max": 1000, "unit": "mg"},
        "source": "cima",
        "country": "ES",
    },
    {
        "active_ingredient": "omeprazol",
        "brand_name": "Losec",
        "presentation": "cápsula 20 mg",
        "concentration": "20 mg",
        "form": "capsula",
        "dose_range": {"min": 10, "max": 40, "unit": "mg"},
        "source": "cima",
        "country": "ES",
    },
    {
        "active_ingredient": "metformina",
        "brand_name": "Glucophage",
        "presentation": "comprimido 850 mg",
        "concentration": "850 mg",
        "form": "comprimido",
        "dose_range": {"min": 500, "max": 2000, "unit": "mg"},
        "source": "digemid",
        "country": "PE",
    },
    {
        "active_ingredient": "atorvastatina",
        "brand_name": "Lipitor",
        "presentation": "comprimido 20 mg",
        "concentration": "20 mg",
        "form": "comprimido",
        "dose_range": {"min": 10, "max": 80, "unit": "mg"},
        "source": "digemid",
        "country": "PE",
    },
    {
        "active_ingredient": "losartan",
        "brand_name": "Cozaar",
        "presentation": "comprimido 50 mg",
        "concentration": "50 mg",
        "form": "comprimido",
        "dose_range": {"min": 25, "max": 100, "unit": "mg"},
        "source": "cima",
        "country": "ES",
    },
    {
        "active_ingredient": "azitromicina",
        "brand_name": "Zithromax",
        "presentation": "comprimido 500 mg",
        "concentration": "500 mg",
        "form": "comprimido",
        "dose_range": {"min": 250, "max": 500, "unit": "mg"},
        "source": "digemid",
        "country": "PE",
    },
]


def get_seed_catalog() -> list[CatalogItem]:
    items = []
    for entry in _SEED_DATA:
        item_id = make_id(entry["source"], entry["active_ingredient"], entry["presentation"])
        items.append(CatalogItem(id=item_id, **entry))
    return items
