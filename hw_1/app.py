import streamlit as st
import pandas as pd
import plotly.express as px
from temperature_analysis import analyze_temperature, detect_anomalies
import asyncio

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
