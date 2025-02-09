import requests
from loguru import logger
from config import OPENWEATHER_API_KEY, CALORIENINJAS_API_KEY, API_NINJAS_CALORIES_BURNED_API_KEY

def get_temperature(city: str) -> float:
    """
    Получение температуры для указанного города через OpenWeatherMap Weather API.
    """
    url = "http://api.openweathermap.org/data/2.5/weather"
    params = {"q": city, "appid": OPENWEATHER_API_KEY, "units": "metric"}
    try:
        response = requests.get(url, params=params, timeout=5)
        data = response.json()
        temp = data["main"]["temp"]
        return temp
    except Exception as e:
        logger.error(f"Ошибка получения температуры для {city}: {e}")
        return 20.0

async def get_food_nutrition(food_name: str) -> (int, dict):
    """
    Получение калорийности пищи через CalorieNinjas Nutrition API.
    """
    url = "https://api.calorieninjas.com/v1/nutrition"
    headers = {
        "X-Api-Key": CALORIENINJAS_API_KEY
    }
    params = {"query": food_name}
    try:
        response = requests.get(url, headers=headers, params=params, timeout=5)
        data = response.json()
        items = data.get("items")
        if items and len(items) > 0:
            item = items[0]
            return 0, {"name": item.get("name", food_name), "calories": item.get("calories", 0)}
        else:
            logger.error(f"Данные по питательности для '{food_name}' не найдены")
            return 1, {}
    except Exception as e:
        logger.error(f"Ошибка получения данных по питательности для '{food_name}': {e}")
        return 1, {}

async def get_workout_calories_burned(workout_name: str, weight: float, duration: int) -> (int, dict):
    """
    Получение данных о сожжённых калориях через API Ninjas Calories Burned API.
    """
    url = "https://api.api-ninjas.com/v1/caloriesburned"
    headers = {
        "X-Api-Key": API_NINJAS_CALORIES_BURNED_API_KEY
    }
    params = {"activity": workout_name, "weight": weight, "duration": duration}
    try:
        response = requests.get(url, headers=headers, params=params, timeout=5)
        data = response.json()
        if isinstance(data, list) and len(data) > 0:
            workout_data = data[0]
            return 0, {"name": workout_data.get("name", workout_name), "calories": workout_data.get("calories", 0)}
        else:
            logger.error(f"Данные по тренировке для '{workout_name}' не найдены")
            return 1, {}
    except Exception as e:
        logger.error(f"Ошибка получения данных по тренировке для '{workout_name}': {e}")
        return 1, {}

def calculate_calorie_goal(weight: float, height: float, age: int, activity: int) -> float:
    """
    Вычисление калорийной цели на основе базового метаболизма и уровня активности.
    """
    bmr = 10 * weight + 6.25 * height - 5 * age + 5  # упрощённая формула (для мужчин)
    extra = (activity // 30) * 200
    return bmr + extra

def calculate_water_target(weight: float, activity: int, temperature: float) -> float:
    """
    Вычисление нормы воды: вес (кг) × 30 мл, плюс 500 мл за каждые 30 мин активности.
    При температуре выше 25°C добавляется дополнительная вода.
    """
    water = weight * 30 + (activity // 30) * 500
    if temperature > 25:
        water += 500 if temperature < 30 else 1000
    return water
