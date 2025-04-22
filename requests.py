from aiohttp import ClientSession, ClientTimeout

from retry import retry_request


@retry_request(default_value=str(), raise_error=True, attempts=5, delay=5)
async def parse_prices(session: ClientSession, data: dict) -> tuple[str, int, str]:
    async with session.post(
            url='https://discounts-prices.wildberries.ru/ns/dp-api/discounts-prices/suppliers/api/v1/list/goods/filter',
            json=data,
            timeout=ClientTimeout(total=15)
    ) as response:
        return str(response.url), response.status, await response.text()


@retry_request(default_value=str(), raise_error=True, attempts=5, delay=30)
async def set_prices(session: ClientSession, data: dict) -> tuple[str, int, str]:
    async with session.post(
            url='https://discounts-prices-api.wildberries.ru/api/v2/upload/task',
            json=data,
            timeout=ClientTimeout(total=15)
    ) as response:
        return str(response.url), response.status, await response.text()
