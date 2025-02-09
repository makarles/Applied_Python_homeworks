from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from loguru import logger

from db import save_profile
from utils import calculate_calorie_goal, calculate_water_target, get_temperature

profile_router = Router()


class ProfileStates(StatesGroup):
    weight = State()
    height = State()
    age = State()
    activity = State()
    city = State()
    calorie_goal = State()


@profile_router.message(Command("set_profile"))
async def set_profile_start(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Введите ваш вес (в кг):")
    await state.set_state(ProfileStates.weight)


@profile_router.message(ProfileStates.weight)
async def set_profile_weight(message: Message, state: FSMContext):
    try:
        weight = float(message.text)
    except ValueError:
        await message.answer("Пожалуйста, введите корректное число для веса.")
        return
    await state.update_data(weight=weight)
    await message.answer("Введите ваш рост (в см):")
    await state.set_state(ProfileStates.height)


@profile_router.message(ProfileStates.height)
async def set_profile_height(message: Message, state: FSMContext):
    try:
        height = float(message.text)
    except ValueError:
        await message.answer("Пожалуйста, введите корректное число для роста.")
        return
    await state.update_data(height=height)
    await message.answer("Введите ваш возраст:")
    await state.set_state(ProfileStates.age)


@profile_router.message(ProfileStates.age)
async def set_profile_age(message: Message, state: FSMContext):
    try:
        age = int(message.text)
    except ValueError:
        await message.answer("Пожалуйста, введите корректное число для возраста.")
        return
    await state.update_data(age=age)
    await message.answer("Сколько минут активности у вас в день?")
    await state.set_state(ProfileStates.activity)


@profile_router.message(ProfileStates.activity)
async def set_profile_activity(message: Message, state: FSMContext):
    try:
        activity = int(message.text)
    except ValueError:
        await message.answer("Пожалуйста, введите корректное число для активности.")
        return
    await state.update_data(activity=activity)
    await message.answer("В каком городе вы находитесь?")
    await state.set_state(ProfileStates.city)


@profile_router.message(ProfileStates.city)
async def set_profile_city(message: Message, state: FSMContext):
    city = message.text
    await state.update_data(city=city)
    await message.answer("Если хотите задать цель по калориям вручную, введите её, иначе отправьте 'нет':")
    await state.set_state(ProfileStates.calorie_goal)


@profile_router.message(ProfileStates.calorie_goal)
async def set_profile_calorie_goal(message: Message, state: FSMContext):
    data = await state.get_data()
    weight = data.get("weight")
    height = data.get("height")
    age = data.get("age")
    activity = data.get("activity")
    city = data.get("city")
    default_calories = calculate_calorie_goal(weight, height, age, activity)
    if message.text.strip().lower() == "нет":
        calorie_goal = default_calories
    else:
        try:
            calorie_goal = float(message.text)
        except ValueError:
            await message.answer("Некорректное значение. Будет использовано значение по умолчанию.")
            calorie_goal = default_calories

    temperature = get_temperature(city)
    water_target = calculate_water_target(weight, activity, temperature)

    await save_profile(
        user_id=message.from_user.id,
        weight=weight,
        height=height,
        age=age,
        activity=activity,
        city=city,
        water_target=water_target,
        calorie_target=calorie_goal,
    )

    await message.answer(
        f"Профиль сохранён!\nНорма воды: {water_target:.0f} мл\nКалорийная цель: {calorie_goal:.0f} ккал"
    )
    await state.clear()
