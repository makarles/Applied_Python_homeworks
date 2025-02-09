import asyncio
from aiogram import Bot, Dispatcher, Router
from aiogram.filters import Command, CommandStart, CommandObject
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from loguru import logger

from config import BOT_TOKEN, LoggingMiddleware
from profile import profile_router
from db import (
    log_water, log_consumed_calories, log_burned_calories,
    get_progress, get_user_weight, increase_water_target
)
from utils import get_food_nutrition, get_workout_calories_burned

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
dp.include_router(profile_router)
dp.message.outer_middleware(LoggingMiddleware())

@dp.message(CommandStart())
async def start_command(message: Message):
    """Начало взаимодействия с ботом."""
    await message.answer(
        '👋 Привет! Я — бот, позволяющий отслеживать потребление воды и расход калорий.\n'
        'Используйте команду /help для просмотра списка поддерживаемых команд.'
    )

@dp.message(Command('help'))
async def help_command(message: Message):
    """Справка по возможностям бота."""
    await message.answer(
        'Я могу помочь в отслеживании потребления воды и расхода калорий.\n'
        'Список реализованных команд:\n'
        '🔐 /set_profile — настроить профиль пользователя (очищает все сохранённые ранее данные);\n'
        '💧 /log_water <объём воды в мл> — записать потребление воды;\n'
        '🌭 /log_food <название блюда на английском> <размер порции в г> — записать приём пищи;\n'
        '🏃 /log_workout <тип тренировки на английском> <время в мин> — записать физическую тренировку;\n'
        '📊 /check_progress — вывести прогресс в выполнении дневных целей;\n'
        '❌ /cancel — отменить текущее действие.'
    )

@dp.message(Command('cancel'))
async def cancel_command(message: Message, state: FSMContext):
    """Сброс текущего состояния (отмена действия)."""
    current_state = await state.get_state()
    if current_state is None:
        await message.answer('❌ В данный момент нечего отменять')
    else:
        await state.clear()
        await message.answer('✅ Действие отменено')

@dp.message(Command('log_water'))
async def log_water_command(message: Message, command: CommandObject):
    """Логирование потребления воды."""
    water_volume = command.args
    if water_volume is None:
        await message.answer('❌ Отсутствует объём потреблённой воды (в мл)')
        return
    try:
        water_volume = int(water_volume)
    except ValueError:
        await message.answer('❌ Передано некорректное значение объёма воды')
        return
    if water_volume < 0 or water_volume > 3000:
        await message.answer('❌ Введённый объём воды выходит из допустимого диапазона (0, 3000) мл')
        return
    try:
        await log_water(message.from_user.id, water_volume)
    except KeyError:
        await message.answer('❌ Профиль пользователя не настроен! Сначала используйте команду /set_profile.')
        return
    data = await get_progress(message.from_user.id)
    await message.answer(
        '💧 Выпитая вода записана! '
        f'💦 Прогресс за день: {data["logged_water"]}/{data["water_target"]} мл.'
    )

class ConfirmationState(StatesGroup):
    awaiting_confirmation = State()

@dp.message(Command('log_food'))
async def log_food_command(message: Message, command: CommandObject, state: FSMContext):
    """Логирование приёма пищи."""
    if command.args is None:
        await message.answer('❌ Отсутствуют название и количество пищи')
        return
    try:
        args = command.args.split()
        food_name = " ".join(args[:-1])
        serving_size = int(args[-1])
    except ValueError:
        await message.answer('❌ Некорректный формат входных данных, введите данные в формате:\n'
                             '/log_food <название блюда на английском> <размер порции в г>')
        return
    if serving_size < 0 or serving_size > 1000:
        await message.answer('❌ Введённый размер порции выходит из допустимого диапазона (0, 1000) г')
        return
    status, food_data = await get_food_nutrition(food_name)
    if status != 0:
        await message.answer('❌ Ошибка получения калорийности пищи')
        return
    calories = food_data['calories'] / 100 * serving_size
    await state.update_data(mode='food', calories=calories)
    await state.set_state(ConfirmationState.awaiting_confirmation)
    await message.answer(
        '🌭 Найденная еда:\n'
        f'Название: {food_data["name"]}\n'
        f'Размер порции: {serving_size} г\n'
        f'Общая калорийность: {calories} ккал\n'
        'Всё верно? (да✅/нет❌)'
    )

@dp.message(Command('log_workout'))
async def log_workout_command(message: Message, command: CommandObject, state: FSMContext):
    """Логирование тренировки."""
    if command.args is None:
        await message.answer('❌ Отсутствуют название и продолжительность тренировки')
        return
    try:
        args = command.args.split()
        workout_name = " ".join(args[:-1])
        duration = int(args[-1])
    except ValueError:
        await message.answer('❌ Некорректный формат входных данных, введите данные в формате:\n'
                             '/log_workout <тип тренировки на английском> <время в мин>')
        return
    if duration < 0 or duration > 1440:
        await message.answer('❌ Введённая продолжительность тренировки выходит из допустимого диапазона (0, 1440) мин')
        return
    try:
        weight = await get_user_weight(message.from_user.id)
    except KeyError:
        await message.answer('❌ Профиль пользователя не настроен! Сначала используйте команду /set_profile.')
        return
    status, workout_data = await get_workout_calories_burned(workout_name, weight, duration)
    if status != 0:
        await message.answer('❌ Ошибка получения интенсивности тренировки')
        return
    await state.update_data(mode='workout', calories=workout_data['calories'], duration=duration)
    await state.set_state(ConfirmationState.awaiting_confirmation)
    await message.answer(
        '🏃 Найденная тренировка:\n'
        f'Название: {workout_data["name"]}\n'
        f'Длительность: {duration} мин\n'
        f'Потраченные калории: {workout_data["calories"]} ккал\n'
        'Всё верно? (да✅/нет❌)'
    )

@dp.message(ConfirmationState.awaiting_confirmation)
async def confirm_message(message: Message, state: FSMContext):
    """Подтверждение записи еды и тренировок."""
    try:
        if message.text.lower() in ('да', 'yes'):
            data = await state.get_data()
            calories = data['calories']
            if data['mode'] == 'food':
                await log_consumed_calories(message.from_user.id, calories)
                p_data = await get_progress(message.from_user.id)
                await state.clear()
                await message.answer(
                    '🌭 Приём пищи записан! '
                    f'😋 Прогресс за день: {p_data["logged_calories"]}/{p_data["calorie_target"]} ккал.'
                )
            else:
                await log_burned_calories(message.from_user.id, calories)
                extra_water = 200 * (data['duration'] // 30)
                await increase_water_target(message.from_user.id, extra_water)
                p_data = await get_progress(message.from_user.id)
                await state.clear()
                await message.answer(
                    f'🏃 Тренировка записана! 💧 Добавлено {extra_water} мл воды к дневной цели.\n'
                    f'🔥 Сожжено за день: {p_data["burned_calories"]} ккал\n'
                    f'💦 Вода за день: {p_data["logged_water"]}/{p_data["water_target"]} мл'
                )
        elif message.text.lower() in ('нет', 'no'):
            await state.clear()
            await message.answer('✅ Запись отменена')
        else:
            await message.answer('❌ Ответ не распознан, повторите попытку')
    except KeyError:
        await state.clear()
        await message.answer('❌ Профиль пользователя не настроен! Сначала используйте команду /set_profile.')

@dp.message(Command('check_progress'))
async def check_progress_command(message: Message):
    """Вывод прогресса в выполнении дневных целей."""
    try:
        data = await get_progress(message.from_user.id)
    except KeyError:
        await message.answer('❌ Профиль пользователя не настроен! Сначала используйте команду /set_profile.')
        return
    await message.answer(
        '📊 Дневной прогресс:\n'
        f'💦 Вода: выпито {data["logged_water"]}/{data["water_target"]} мл.\n'
        'Калории:\n'
        f'😋 Поглощено {data["logged_calories"]}/{data["calorie_target"]} ккал;\n'
        f'🔥 Сожжено {data["burned_calories"]} ккал.'
    )

final_router = Router()
dp.include_router(final_router)

@final_router.message()
async def unrecognized_message(message: Message):
    """Обработка не пойманных ранее сообщений."""
    logger.error(f'Команда не распознана: "{message.text}"')
    await message.answer(f'❌ Команда не распознана: "{message.text}"')

async def main() -> None:
    """Основная функция для запуска бота."""
    try:
        logger.info('Polling запущен')
        await dp.start_polling(bot)
    finally:
        logger.info('Polling прекращён')
        await bot.session.close()

if __name__ == '__main__':
    asyncio.run(main())
