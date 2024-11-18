from pydantic import BaseModel

from src.settings import get_settings
from src.utils.aiohttpt_client import AiohttpClient, get_aiohttp_client


class GeocodeResult(BaseModel):
    lat: str
    lon: str
    importance: float


class GeocodeClient:
    """Клиент для гео-кодинг API https://geocode.maps.co/"""

    HOST = "https://geocode.maps.co"
    PATH = "/search"

    def __init__(self, token: str):
        self.__token: str = token
        self.__client: AiohttpClient = get_aiohttp_client()

    async def get_coordinates(self, address: str) -> list[GeocodeResult]:
        """Метод для получения координат по адресу

        Args:
            address (str): Адрес на английском языке

        Returns:
            list[GeocodeResult]: Список возможных точек
        """
        url = self.HOST + self.PATH
        params = {"api_key": self.__token, "q": address}
        results = await self.__client.make_request(method="GET", url=url, params=params)
        results = [GeocodeResult(**i) for i in results]
        return results


settings = get_settings()
geocode_client = GeocodeClient(settings.GEOCODE_API_KEY)
