
users_db = {}

async def save_profile(user_id: int, weight: float, height: float, age: int, activity: int,
                       city: str, water_target: float, calorie_target: float):
    users_db[user_id] = {
        "weight": weight,
        "height": height,
        "age": age,
        "activity": activity,
        "city": city,
        "water_target": water_target,
        "calorie_target": calorie_target,
        "logged_water": 0,
        "logged_calories": 0,
        "burned_calories": 0,
    }

async def log_water(user_id: int, volume: int):
    if user_id not in users_db:
        raise KeyError("Профиль не найден")
    users_db[user_id]["logged_water"] += volume

async def log_consumed_calories(user_id: int, calories: float):
    if user_id not in users_db:
        raise KeyError("Профиль не найден")
    users_db[user_id]["logged_calories"] += calories

async def log_burned_calories(user_id: int, calories: float):
    if user_id not in users_db:
        raise KeyError("Профиль не найден")
    users_db[user_id]["burned_calories"] += calories

async def get_progress(user_id: int) -> dict:
    if user_id not in users_db:
        raise KeyError("Профиль не найден")
    return users_db[user_id]

async def get_user_weight(user_id: int) -> float:
    if user_id not in users_db:
        raise KeyError("Профиль не найден")
    return users_db[user_id]["weight"]

async def increase_water_target(user_id: int, extra_water: int):
    if user_id not in users_db:
        raise KeyError("Профиль не найден")
    users_db[user_id]["water_target"] += extra_water
