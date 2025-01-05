import aiohttp


async def fetch_temperature(city: str, api_key: str) -> (int, float | str):
    """
    Асинхронная функция для получения текущей температуры через OpenWeatherMap API.

    Возвращает:
    - (0, температура): если запрос успешен.
    - (-1, сообщение об ошибке): если произошла ошибка.
    """
    url = f"http://api.openweathermap.org/data/2.5/weather"
    params = {'q': city, 'appid': api_key, 'units': 'metric'}

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return 0, data['main']['temp']
                else:
                    return -1, await response.text()
    except aiohttp.ClientError as e:
        return -1, str(e)
