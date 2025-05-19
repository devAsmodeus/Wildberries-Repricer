import os
import json
import asyncio
import traceback
import os.path
import numpy as np
import pandas as pd

from tqdm import tqdm
from aiohttp import TCPConnector
from datetime import datetime, timedelta
from dotenv import load_dotenv

from telethon.sync import TelegramClient
from telethon.sessions import StringSession
from telethon.tl.types import InputPeerUser

from requests import *
from emulator import get_coefficient

import scmRepricer

COEFFICIENT_LIMIT = 15_330.0


async def start_script():
    api_id, api_hash, session_string = get_env_variables()
    message = scmRepricer.MessageModel(**{
        'API_ID': int(api_id),
        'API_HASH': api_hash,
        'SESSION_STRING': session_string,
        'scriptName': 'Обновление цен карточек Wildberries',
        'startTime': datetime.now(),
        'runTime': None,
        'users': ['Azat747', 'AsmodeusGL'],
        'error': False,
        'errorText': None,
        'message': None
    })
    try:
        message = await main(message)
    except Exception as exception:
        message.error = True
        message.errorText = repr(exception) + f'\n{traceback.format_exc()}'
        message.runTime = datetime.now() - message.startTime
        message.message = (
            f'⚠ ВНИМАНИЕ! Сообщение об ошибке ⚠\n\nСкрипт: {message.scriptName}\n'
            f'Время работы программы: {message.runTime}\nОшибка: {message.errorText}'
        )
    finally:
        print(message.message)
        # await send_report(message)


async def main(message: scmRepricer.MessageModel) -> scmRepricer.MessageModel:
    headers, connector = get_headers(False), TCPConnector(ssl=False)
    async with ClientSession(headers=headers, connector=connector) as session:
        coefficient = get_coefficient()
        prices = await get_prices(session)
        prices = format_prices(prices, coefficient)
        count_edit_prices = await upload_prices(prices)
    message.runTime = datetime.now() - message.startTime
    message.message = (
        f'✅ Скрипт успешно завершён ✅\n\nСкрипт: {message.scriptName}\n'
        f'Время работы программы: {message.runTime}\n'
        f'Количество обновленных карточек: {count_edit_prices}'
    )
    return message


async def upload_prices(prices: dict[int, scmRepricer.CardPriceEditModel]) -> int:
    result = list()
    df = pd.read_excel(
        get_filename(), sheet_name='Цены', engine='openpyxl',
        # dtype={'Артикул WB': int, 'МРЦ': int}
    )
    pd.DataFrame.replace(df, {np.nan: None, '': None}, inplace=True)
    for _, row in df.iterrows():
        if all([nm_id := row['Артикул WB'], excel_price := row['МРЦ']]) and nm_id in prices:
            # if nm_id != 235786068:
            #     continue
            edit_model, nm_id, excel_price = prices[nm_id], int(nm_id), int(excel_price)
            discount, discount_site = edit_model.discount, edit_model.discountSite
            discount = discount if discount else 50
            edit_price = (
                excel_price / edit_model.coefficientWallet if excel_price < COEFFICIENT_LIMIT else excel_price
            )
            discount_price = edit_price / ((100 - (discount_site if discount_site else 0)) / 100)
            edit_price = round(discount_price / (100 - discount) * 100) + 6
            if edit_price != edit_model.price:
                result.append({"nmID": nm_id, "price": edit_price, "discount": discount})
    else:
        if result:
            return await update_prices(result)
        else:
            return 0


async def update_prices(data: list[dict]) -> int:
    headers, connector = get_headers(True), TCPConnector(ssl=False)
    async with ClientSession(headers=headers, connector=connector) as session:
        for part in tqdm(range(0, len(data), block := 100), desc='Загрузка цен'):
            payload_data = {"data": data[part:part+block]}
            await set_prices(session, payload_data)
        else:
            return len(data)


def format_prices(
        prices: list[scmRepricer.CardPriceModel],
        coefficient: float
) -> dict[int, scmRepricer.CardPriceEditModel]:
    result = dict()
    for card in prices:
        for price, discount_price, club_price in zip(card.prices, card.discountedPrices, card.clubDiscountedPrices):
            result[card.nmID] = scmRepricer.CardPriceEditModel(**{
                'price': price,
                'discount': card.discount,
                'discountSite': card.discountOnSite,
                'coefficientWallet': coefficient
            })
            break
    else:
        return result


async def get_prices(session: ClientSession) -> list[scmRepricer.CardPriceModel]:
    result, data = list(), {
        "limit": 1000, "offset": 0, "facets": [], "filterWithoutPrice": False,
        "filterWithLeftovers": True, "sort": "price", "sortOrder": 0
    }
    while True:
        *_, prices = await parse_prices(session, data)
        prices = json.loads(prices).get('data', dict()).get('listGoods', list())
        if prices:
            result.extend([scmRepricer.CardPriceModel(**card) for card in prices])
            data['offset'] += 1000
        else:
            return result


def get_filename() -> str:
    # filename = r'C:/Programs/Запись цен.xlsx'
    filename = r'./Запись цен.xlsx'
    if not os.path.exists(filename):
        raise FileNotFoundError('Файл не найден')
    else:
        return filename


def get_headers(is_api: bool) -> dict[str, str]:
    if is_api:
        return {
            'Content-Type': 'application/json',
            'Authorization': os.getenv('AUTHORIZATION')
        }
    else:
        return {
            'accept': '*/*',
            'accept-encoding': 'gzip, deflate, br, zstd',
            'accept-language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
            'authorizev3': os.getenv('AUTHORIZATIONV3'),
            'content-type': 'application/json',
            'cookie': os.getenv('COOKIE'),
            'priority': 'u=1, i',
            'user-agent': (
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                '(KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36'
            )
        }


def get_env_variables() -> tuple[str, str, str]:
    dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
    if os.path.exists(dotenv_path):
        load_dotenv(dotenv_path)
        return (
            os.getenv("API_ID"),
            os.getenv("API_HASH"),
            os.getenv("STRING_SESSION")
        )
    else:
        raise FileNotFoundError('Файл с переменными не найден')


async def send_report(message: scmRepricer.MessageModel) -> None:
    async with TelegramClient(StringSession(message.SESSION_STRING), message.API_ID, message.API_HASH) as client:
        for user in message.users:
            user_info = await client.get_entity(user)
            receiver = InputPeerUser(user_info.id, user_info.access_hash)
            await client.send_message(receiver, message.message, silent=True)
            await asyncio.sleep(3)


if __name__ == "__main__":
    asyncio.run(start_script())
