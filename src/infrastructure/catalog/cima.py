import httpx
from tenacity import retry, retry_if_exception, stop_after_attempt, wait_exponential

from src.domain.entities.catalog_item import CatalogItem
from src.domain.services.make_id import make_id


def _is_retryable(exc: BaseException) -> bool:
    if isinstance(exc, httpx.HTTPStatusError):
        return exc.response.status_code in (429, 500, 502, 503, 504)
    return isinstance(exc, (httpx.TimeoutException, httpx.ConnectError))


class CimaClient:
    BASE_URL = "https://cima.aemps.es/cima/rest"

    def __init__(self, timeout: float = 30.0) -> None:
        self._timeout = timeout

    async def search(self, query: str, page: int = 1, page_size: int = 25) -> list[CatalogItem]:
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            data = await self._get_page(
                client, {"nombre": query, "pagina": page, "tamanioPagina": page_size}
            )
            return [self._map_to_item(r) for r in data.get("resultados", [])]

    async def fetch_all(self, limit: int | None = None) -> list[CatalogItem]:
        items: list[CatalogItem] = []
        page = 1
        page_size = 25
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            while True:
                data = await self._get_page(client, {"pagina": page, "tamanioPagina": page_size})
                resultados = data.get("resultados", [])
                if not resultados:
                    break
                items.extend(self._map_to_item(r) for r in resultados)
                if limit and len(items) >= limit:
                    return items[:limit]
                total = data.get("totalFilas", 0)
                if len(items) >= total:
                    break
                page += 1
        return items

    @retry(
        wait=wait_exponential(multiplier=1, min=1, max=10),
        stop=stop_after_attempt(3),
        retry=retry_if_exception(_is_retryable),
        reraise=True,
    )
    async def _get_page(self, client: httpx.AsyncClient, params: dict) -> dict:
        response = await client.get(f"{self.BASE_URL}/medicamentos", params=params)
        response.raise_for_status()
        return response.json()

    def _map_to_item(self, raw: dict) -> CatalogItem:
        nregistro = str(raw.get("nregistro", ""))
        return CatalogItem(
            id=make_id("cima", nregistro),
            active_ingredient=raw.get("pactivos", "").strip() or raw.get("nombre", ""),
            brand_name=raw.get("nombre"),
            presentation=raw.get("nombre", ""),
            source="cima",
            country="ES",
        )
