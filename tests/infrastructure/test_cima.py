from unittest.mock import AsyncMock, patch

from src.infrastructure.catalog.cima import CimaClient

SAMPLE_RESPONSE_P1 = {
    "totalFilas": 100,
    "pagina": 1,
    "tamanioPagina": 25,
    "resultados": [
        {"nregistro": "12345", "nombre": "AMOXICILINA 500MG CÁPSULAS", "pactivos": "AMOXICILINA"},
        {"nregistro": "67890", "nombre": "IBUPROFENO 400MG COMPRIMIDOS", "pactivos": "IBUPROFENO"},
    ],
}

SAMPLE_RESPONSE_P2 = {
    "totalFilas": 100,
    "pagina": 2,
    "tamanioPagina": 25,
    "resultados": [],
}


async def test_search_maps_response_correctly():
    client = CimaClient()
    with patch.object(client, "_get_page", new=AsyncMock(return_value=SAMPLE_RESPONSE_P1)):
        items = await client.search("amoxicilina")
    assert len(items) == 2
    assert all(i.source == "cima" for i in items)
    assert all(i.country == "ES" for i in items)


async def test_fetch_all_stops_when_results_empty():
    client = CimaClient()
    mock = AsyncMock(side_effect=[SAMPLE_RESPONSE_P1, SAMPLE_RESPONSE_P2])
    with patch.object(client, "_get_page", new=mock):
        items = await client.fetch_all()
    assert len(items) == 2


async def test_map_to_item_id_deterministic():
    client = CimaClient()
    raw = {"nregistro": "99999", "nombre": "PARACETAMOL 500MG", "pactivos": "PARACETAMOL"}
    id1 = client._map_to_item(raw).id
    id2 = client._map_to_item(raw).id
    assert id1 == id2


async def test_map_to_item_active_ingredient_from_pactivos():
    client = CimaClient()
    raw = {"nregistro": "12345", "nombre": "AMOXICILINA 500MG CÁPSULAS", "pactivos": "AMOXICILINA"}
    item = client._map_to_item(raw)
    assert item.active_ingredient == "AMOXICILINA"
