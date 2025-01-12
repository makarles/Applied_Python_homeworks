import aiohttp
import streamlit as st
import pandas as pd
import plotly.express as px
import asyncio
from time import time

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

def detect_anomalies(city_data, season_stats):
    """
    Определяет аномалии в данных по температуре.

    Аргументы:
    - city_data: DataFrame с данными о температуре.
    - season_stats: DataFrame с сезонной статистикой (mean, std).

    Возвращает:
    - DataFrame с добавленной колонкой `is_anomaly`.
    """
    city_data = city_data.copy()
    city_data['is_anomaly'] = False  # Изначально помечаем все как нормальные
    for season, stats in season_stats.iterrows():
        mean_temp = stats['mean']
        std_temp = stats['std']
        lower_bound = mean_temp - 2 * std_temp
        upper_bound = mean_temp + 2 * std_temp

        # Помечаем аномалии
        is_season = city_data['season'] == season
        city_data.loc[is_season, 'is_anomaly'] = ~city_data[is_season]['temperature'].between(lower_bound, upper_bound)

    # Добавляем скользящее среднее
    city_data['rolling_mean'] = city_data['temperature'].rolling(window=30, center=True).mean()
    return city_data

async def analyze_temperature(city_data, selected_city, api_key, season_stats):
    """
    Асинхронная функция для анализа текущей температуры в городе.

    Аргументы:
    - city_data: данные по городу из CSV.
    - selected_city: выбранный город.
    - api_key: ключ API OpenWeatherMap.
    - season_stats: статистики по сезонам.
    """
    try:
        # Получаем текущую температуру через API
        status, result = await fetch_temperature(selected_city, api_key)
        if status == 0:
            current_temp = result
            st.write(f'Текущая температура: {current_temp} °C')

            # Сравниваем с историческими данными
            current_season = city_data['season'].iloc[-1]
            mean_temp = season_stats.loc[current_season, 'mean']
            std_temp = season_stats.loc[current_season, 'std']
            if mean_temp - 2 * std_temp <= current_temp <= mean_temp + 2 * std_temp:
                st.write("Температура в пределах нормы.")
            else:
                st.write("Температура выходит за пределы нормы!")
        else:
            st.error(f"Ошибка получения температуры: {result}")
    except Exception as e:
        st.error(f"Ошибка: {e}")

def main():
    # Настройка страницы
    st.set_page_config(
        page_title='Температурный анализ и мониторинг',
        layout='wide'
    )

    st.title('Температурный анализ и мониторинг')

    # Загрузка файла с данными
    st.header('Загрузка данных')
    file_upload = st.file_uploader('Загрузите файл с историческими данными', type=['csv'])

    # Проверка наличия файла
    if file_upload is not None:
        try:
            # Попытка загрузить данные
            data = pd.read_csv(file_upload)

            # Проверка на наличие необходимых колонок
            required_columns = {'city', 'timestamp', 'temperature', 'season'}
            if not required_columns.issubset(data.columns):
                st.error(f'Файл должен содержать следующие колонки: {", ".join(required_columns)}')
                return
            else:
                st.success("Данные успешно загружены!")
        except Exception as e:
            st.error(f"Ошибка при чтении файла: {e}")
            return
    else:
        st.info("Пожалуйста, загрузите CSV-файл с историческими данными.")
        return

    # Преобразование данных
    data['timestamp'] = pd.to_datetime(data['timestamp'])  # Преобразуем timestamp в datetime

    # Выбор города
    cities = data['city'].unique()
    selected_city = st.selectbox("Выберите город для анализа", cities)
    city_data = data[data['city'] == selected_city]

    # Ввод API ключа
    api_key = st.text_input('Введите API ключ OpenWeatherMap для текущей температуры')

    # Расчёт статистики
    st.subheader(f'Статистика по городу: {selected_city}')
    season_stats = city_data.groupby('season')['temperature'].agg(['mean', 'std'])
    st.dataframe(season_stats)

    # Добавление аномалий
    city_data = detect_anomalies(city_data, season_stats)

    # Визуализация временных рядов с точками
    st.subheader(f'Временные ряды температуры для города: {selected_city}')

    # Разделяем данные на нормальные и аномальные
    not_anomalies = city_data[city_data['is_anomaly'] == False]
    anomalies = city_data[city_data['is_anomaly'] == True]

    # Создаём график с Plotly
    fig = px.scatter(
        city_data,
        x='timestamp',
        y='temperature',
        color='is_anomaly',
        color_discrete_map={False: 'blue', True: 'red'},
        title=f"Временные ряды для {selected_city}",
        labels={'is_anomaly': 'Аномалия'}
    )

    # Добавляем линию скользящего среднего как последний слой
    fig.add_scatter(
        x=city_data['timestamp'],
        y=city_data['rolling_mean'],
        mode='lines',
        line=dict(color='lime', width=5),
        name='Скользящее среднее'
    )

    # Настройки осей и легенды
    fig.update_layout(
        xaxis_title="Дата",
        yaxis_title="Температура (°C)",
        legend_title="Тип данных",
        template="plotly_white",
        height=500
    )

    # Отображение графика
    st.plotly_chart(fig)

    # Анализ текущей температуры
    if api_key:
        st.subheader(f'Текущая температура в городе: {selected_city}')
        try:
            asyncio.run(analyze_temperature(city_data, selected_city, api_key, season_stats))
        except Exception as e:
            st.error(f"Ошибка при получении текущей температуры: {e}")
    else:
        st.warning("Введите API-ключ для получения текущей температуры.")

if __name__ == "__main__":
    main()
