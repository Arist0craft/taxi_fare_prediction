from functools import lru_cache
from typing import Any

import aiohttp


class AiohttpClient:
    """Обёртка для AioHttp ClientSession"""

    def __init__(self):
        self.session: aiohttp.ClientSession = None

    async def make_request(
        self,
        method: str,
        url: str,
        params: dict[str, str] | None = None,
        json: dict[str, str] | None = None,
    ) -> dict[str, Any] | list[Any]:
        """Соверешение запроса к url

        Args:
            method (str): Метод запроса: GET, POST, PUT, HEADER, DELETE, etc...
            url (str): URL куда идёт запрос
            params (dict[str, str] | None, optional): Query параметры запроса. Defaults to None.
            json (dict[str, str] | None, optional): Данные в теле запроса в формате JSON. Defaults to None.

        Returns:
            dict[str, Any] | list[Any] : Результат запроса в формате JSON
        """
        if not self.session:
            self.session = aiohttp.ClientSession()

        async with self.session.request(
            method=method, url=url, params=params, json=json
        ) as resp:
            resp.raise_for_status()
            return await resp.json()

    async def close(self):
        if self.session and not self.session.closed:
            await self.session.close()


@lru_cache
def get_aiohttp_client() -> AiohttpClient:
    return AiohttpClient()
