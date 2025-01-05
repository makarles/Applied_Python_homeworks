rom api import fetch_temperature
import streamlit as st


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
