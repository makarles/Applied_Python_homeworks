# Импорт библиотек
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import requests
import aiohttp
import nest_asyncio
import asyncio
from time import time
from concurrent.futures import ProcessPoolExecutor

nest_asyncio.apply()

# Путь к данным
DATA_PATH = 'temperature_data.csv'

# 1. Загрузка данных
data = pd.read_csv(DATA_PATH)
data['timestamp'] = pd.to_datetime(data['timestamp'])

print("Пример данных:")
display(data.head())

# Проверка отсутствующих значений
print("Пропущенные значения:")
print(data.isnull().sum())

# 2. Скользящее среднее и стандартное отклонение
data['rolling_mean'] = data.groupby('city')['temperature'].transform(lambda x: x.rolling(window=30).mean())
data['rolling_std'] = data.groupby('city')['temperature'].transform(lambda x: x.rolling(window=30).std())

# 3. Выявление аномалий
def is_anomaly(row: pd.Series) -> bool:
    """Проверка строки на аномальность."""
    return (row['temperature'] < row['rolling_mean'] - 2 * row['rolling_std']
            or row['temperature'] > row['rolling_mean'] + 2 * row['rolling_std'])

data['is_anomaly'] = data.apply(is_anomaly, axis=1)

# 4. Визуализация скользящего среднего и аномалий
city = 'Moscow'
not_anomalies = data[(data['city'] == city) & (data['is_anomaly'] == False)]
anomalies = data[(data['city'] == city) & (data['is_anomaly'] == True)]

plt.figure(figsize=(12, 3))
plt.scatter(not_anomalies['timestamp'], not_anomalies['temperature'], s=5, c='blue', label='Норма')
plt.scatter(anomalies['timestamp'], anomalies['temperature'], s=5, c='red', label='Аномалия')
plt.plot(data[data['city'] == city]['timestamp'], data[data['city'] == city]['rolling_mean'], c='green', label='Скользящее среднее')
plt.legend()
plt.title(f'Температура в городе {city}')
plt.xlabel('Дата')
plt.ylabel('Температура (°C)')
plt.show()

# 5. Вычисление статистик для каждого города и сезона
stats = {}
for city in data['city'].unique():
    stats[city] = {}
    for season in data['season'].unique():
        stats[city][season] = {
            'mean': data[(data['city'] == city) & (data['season'] == season)]['temperature'].mean(),
            'std': data[(data['city'] == city) & (data['season'] == season)]['temperature'].std()
        }

print("Статистика для Москвы:")
display(pd.DataFrame(stats['Moscow']))

# 6. Эксперимент 1: Анализ без параллельности
def analyze_data_base() -> pd.DataFrame:
    """Анализ данных без параллельности."""
    df = pd.read_csv(DATA_PATH)
    df['rolling_mean'] = df.groupby('city')['temperature'].transform(lambda x: x.rolling(window=30).mean())
    df['rolling_std'] = df.groupby('city')['temperature'].transform(lambda x: x.rolling(window=30).std())
    df['is_anomaly'] = df.apply(is_anomaly, axis=1)
    return df

start = time()
_ = analyze_data_base()
print(f"Анализ без параллельности: {time() - start:.2f} секунд")

# 7. Эксперимент 2: Анализ с параллельной обработкой
def analyze_city(city):
    """Анализ данных для одного города."""
    city_data = data[data['city'] == city].copy()
    city_data['rolling_mean'] = city_data['temperature'].rolling(window=30).mean()
    city_data['rolling_std'] = city_data['temperature'].rolling(window=30).std()
    city_data['is_anomaly'] = city_data.apply(is_anomaly, axis=1)
    return city_data

def analyze_data_parallel():
    with ProcessPoolExecutor() as executor:
        results = executor.map(analyze_city, data['city'].unique())
    return pd.concat(results)

start = time()
_ = analyze_data_parallel()
print(f"Анализ с параллельной обработкой: {time() - start:.2f} секунд")

# 8. Сравнение синхронных и асинхронных запросов к API OpenWeatherMap
API_KEY = 'your_openweathermap_api_key'
API_URL = 'https://api.openweathermap.org/data/2.5/weather'

# Синхронный запрос
def sync_request(city: str) -> float:
    params = {'q': city, 'appid': API_KEY, 'units': 'metric'}
    response = requests.get(API_URL, params=params)
    return response.json()['main']['temp']

start = time()
sync_temp = sync_request('Moscow')
print(f"Синхронный запрос: {time() - start:.2f} секунд, температура: {sync_temp}°C")

# Асинхронный запрос
async def async_request(city: str) -> float:
    params = {'q': city, 'appid': API_KEY, 'units': 'metric'}
    async with aiohttp.ClientSession() as session:
        async with session.get(API_URL, params=params) as response:
            return (await response.json())['main']['temp']

start = time()
async_temp = asyncio.run(async_request('Moscow'))
print(f"Асинхронный запрос: {time() - start:.2f} секунд, температура: {async_temp}°C")
