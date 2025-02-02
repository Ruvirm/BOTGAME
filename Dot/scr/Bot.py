from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.utils import executor
import asyncio
import json
import os
import random

API_TOKEN = '7998803207:AAFmsl5Ekl2sA__YLjZwPue1h1WLRG2hpk4'

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# Файл для хранения данных
DATA_FILE = 'diplomacy_game.json'

# Функция для инициализации данных, если файл пуст или повреждён
# Функция для инициализации данных, если файл пуст или повреждён
def load_or_initialize_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError:
            print(f"Ошибка при чтении файла {DATA_FILE}, инициализируем данные заново.")
    return {'players': {}, 'countries': {}, 'alliances': {}}  # Добавляем ключ 'alliances'

# Загрузка данных
data = load_or_initialize_data()

# Сохранение данных
def save_data():
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# Пассивный доход с учётом уровней
async def passive_income():
    while True:
        for user_id, player in data['players'].items():
            income_multiplier = 1 + (player['army_level'] + player['economy_level'] + player['culture_level']) * 0.1
            player['budget'] += int(player.get('income', 1000000) * income_multiplier)
        save_data()
        await asyncio.sleep(60)  # Обновление каждую минуту

# Кнопка "Назад"
def back_button():
    return KeyboardButton("Назад")

# Кнопки главного меню
def main_menu_keyboard():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(KeyboardButton("Прокачать страну"))
    keyboard.add(KeyboardButton("Мя"))
    keyboard.add(KeyboardButton("Помощь"))
    return keyboard

# Команда старта
@dp.message_handler(commands=['start'])
async def start_game(message: types.Message):
    user_id = str(message.from_user.id)
    if user_id in data['players']:
        player = data['players'][user_id]
        await message.answer(f"Вы уже зарегистрированы как {player['country']} с бюджетом {player['budget']} долларов.")
    else:
        await message.answer(
            "Добро пожаловать в игру! Напишите 'Выбрать страну' чтобы выбрать страну или 'Создать страну' чтобы создать свою.")

# Выбор свободной страны
@dp.message_handler(lambda message: message.text.lower() == 'выбрать страну')
async def choose_country(message: types.Message):
    user_id = str(message.from_user.id)
    if user_id in data['players']:
        await message.answer("Вы уже выбрали страну.")
        return

    free_countries = [country for country, owner in data['countries'].items() if owner is None]

    if not free_countries:
        await message.answer("Нет доступных стран. Вы можете создать новую, написав 'Создать страну'.")
        return

    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    for country in free_countries:
        keyboard.add(KeyboardButton(country))

    keyboard.add(back_button())  # Добавляем кнопку "Назад"
    await message.answer("Выберите одну из доступных стран:", reply_markup=keyboard)

# Обработка выбора страны
@dp.message_handler(lambda message: message.text in data['countries'] and data['countries'][message.text] is None)
async def handle_country_choice(message: types.Message):
    country_name = message.text
    user_id = str(message.from_user.id)
    username = message.from_user.username

    if country_name in data['countries'] and data['countries'][country_name] is None:
        data['players'][user_id] = {
            'username': username,
            'country': country_name,
            'budget': 100000000,
            'income': 1000000,
            'army_level': 1,
            'economy_level': 1,
            'culture_level': 1
        }
        data['countries'][country_name] = user_id  # Страна теперь закреплена за игроком
        save_data()
        await message.answer(f"Поздравляем! Вы выбрали страну {country_name} и у вас есть 100 миллионов долларов.", reply_markup=ReplyKeyboardRemove())
    else:
        await message.answer(
            "Эта страна недоступна. Попробуйте выбрать другую или создайте свою, написав 'Создать страну'.")

# Создание новой страны
@dp.message_handler(lambda message: message.text.lower() == 'создать страну')
async def create_country(message: types.Message):
    user_id = str(message.from_user.id)
    username = message.from_user.username
    await message.answer("Введите название вашей новой страны:")

    @dp.message_handler()
    async def set_country_name(msg: types.Message):
        country_name = msg.text.strip()
        if country_name in data['countries']:
            await msg.answer("Такая страна уже существует. Попробуйте выбрать другое название.")
        else:
            # Создаём страну и привязываем её к пользователю
            data['countries'][country_name] = user_id
            data['players'][user_id] = {
                'username': username,
                'country': country_name,
                'budget': 100000000,
                'income': 1000000,
                'army_level': 1,
                'economy_level': 1,
                'culture_level': 1
            }
            save_data()
            await msg.answer(f"Страна {country_name} успешно создана и привязана к вашему аккаунту!", reply_markup=ReplyKeyboardRemove())
            await msg.answer("Вы вернулись в главное меню.", reply_markup=main_menu_keyboard())

# Прокачка страны (выбор чего улучшать)
@dp.message_handler(lambda message: message.text.lower() == 'прокачать страну')
async def upgrade_country(message: types.Message):
    user_id = str(message.from_user.id)
    player = data['players'].get(user_id)

    if not player:
        await message.answer("Вы не зарегистрированы в игре. Напишите 'Создать страну' или 'Выбрать страну'.")
        return

    # Проверка, что у игрока есть своя страна
    if player['country'] is None:
        await message.answer("Вы не выбрали страну. Напишите 'Выбрать страну' или 'Создать страну'.")
        return

    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(KeyboardButton("Прокачать армию"))
    keyboard.add(KeyboardButton("Прокачать экономику"))
    keyboard.add(KeyboardButton("Прокачать культуру"))
    keyboard.add(back_button())

    await message.answer("Что вы хотите прокачать?", reply_markup=keyboard)



# Обработка выбора улучшения
@dp.message_handler(lambda message: message.text.lower() in ['прокачать армию', 'прокачать экономику', 'прокачать культуру'])
async def handle_upgrade_choice(message: types.Message):
    user_id = str(message.from_user.id)
    player = data['players'].get(user_id)

    if not player:
        await message.answer("Вы не зарегистрированы в игре. Напишите 'Создать страну' или 'Выбрать страну'.")
        return

    # Проверка на существование страны у игрока
    if 'country' not in player or player['country'] is None:
        await message.answer("Вы не выбрали страну. Напишите 'Выбрать страну' или 'Создать страну'.")
        return

    # Проверка на наличие средств для улучшений
    upgrade_type = message.text.lower().replace("прокачать ", "")
    upgrade_cost = 5000000 * (player['army_level'] + player['economy_level'] + player['culture_level'])

    if player['budget'] < upgrade_cost:
        await message.answer(f"Недостаточно средств для прокачки. Требуется {upgrade_cost} долларов.")
        return

    await message.answer(
        f"Вы хотите прокачать {upgrade_type}? Это стоит {upgrade_cost} долларов. Напишите 'Да' для подтверждения или 'Нет' для отмены.")

    player['upgrade_type'] = upgrade_type
    save_data()


# Подтверждение прокачки
@dp.message_handler(lambda message: message.text.lower() in ['да', 'нет'])
async def confirm_upgrade(message: types.Message):
    user_id = str(message.from_user.id)
    player = data['players'].get(user_id)

    if not player or 'upgrade_type' not in player:
        await message.answer("Вы не выбрали что прокачивать. Напишите 'Прокачать страну' чтобы выбрать улучшение.")
        return

    if message.text.lower() == 'да':
        upgrade_type = player['upgrade_type']
        upgrade_cost = 5000000 * (player['army_level'] + player['economy_level'] + player['culture_level'])

        player['budget'] -= upgrade_cost
        if upgrade_type == 'армию':
            player['army_level'] += 1
        elif upgrade_type == 'экономику':
            player['economy_level'] += 1
        elif upgrade_type == 'культуру':
            player['culture_level'] += 1

        await message.answer(f"Ваш {upgrade_type} успешно прокачан!", reply_markup=ReplyKeyboardRemove())
    else:
        await message.answer("Прокачка отменена.", reply_markup=ReplyKeyboardRemove())

    player.pop('upgrade_type', None)
    save_data()

# Информация о стране
@dp.message_handler(lambda message: message.text.lower() == 'мя')
async def country_info(message: types.Message):
    user_id = str(message.from_user.id)
    player = data['players'].get(user_id)

    if not player:
        await message.answer("Вы не зарегистрированы в игре. Напишите 'Создать страну' или 'Выбрать страну'.")
        return

    country = player['country']
    country_info = (
        f"Страна: {country}\n"
        f"Бюджет: {player['budget']} долларов\n"
        f"Доход: {player['income']} долларов/час\n"
        f"Уровень армии: {player['army_level']}\n"
        f"Уровень экономики: {player['economy_level']}\n"
        f"Уровень культуры: {player['culture_level']}"
    )
    await message.answer(country_info)

# Команда для торговли (обмен денег между игроками альянса)
@dp.message_handler(lambda message: message.text.lower().startswith('торговать с'))
async def trade_with_alliance_member(message: types.Message):
    user_id = str(message.from_user.id)
    player = data['players'].get(user_id)

    if not player or 'alliance' not in player:
        await message.answer("Вы не состоите в альянсе. Напишите 'Создать альянс' или 'Вступить в альянс'.")
        return

    target_country = message.text[len('торговать с '):].strip()
    if target_country == player['country']:
        await message.answer("Вы не можете торговать с собой.")
        return

    # Находим игрока, с которым хотят торговать
    target_player_id = None
    for member in data['alliances'][player['alliance']]:
        if data['players'][member]['country'] == target_country:
            target_player_id = member
            break

    if target_player_id is None:
        await message.answer(f"Страна {target_country} не является частью вашего альянса.")
        return

    # Запрос на сумму обмена
    await message.answer(f"Какую сумму вы хотите обменять с {target_country}?")
    @dp.message_handler()
    async def handle_trade_amount(msg: types.Message):
        amount = int(msg.text)
        if amount > player['budget']:
            await msg.answer("Недостаточно средств для обмена.")
            return

        # Перевод средств между игроками
        data['players'][user_id]['budget'] -= amount
        data['players'][target_player_id]['budget'] += amount
        save_data()
        await msg.answer(f"Вы обменяли {amount} долларов с {target_country}.")


# Создание альянса
@dp.message_handler(lambda message: message.text.lower() == 'создать альянс')
async def create_alliance(message: types.Message):
    user_id = str(message.from_user.id)
    player = data['players'].get(user_id)

    if not player:
        await message.answer("Вы не зарегистрированы в игре. Напишите 'Создать страну' или 'Выбрать страну'.")
        return

    if 'alliance' in player:
        await message.answer("Вы уже состоите в альянсе.")
        return

    await message.answer("Введите название вашего альянса:")

    @dp.message_handler()
    async def set_alliance_name(msg: types.Message):
        alliance_name = msg.text.strip()

        if alliance_name in data['alliances']:
            await msg.answer(f"Альянс с таким названием уже существует. Попробуйте другое название.")
        else:
            data['alliances'][alliance_name] = [user_id]
            player['alliance'] = alliance_name
            save_data()
            await msg.answer(f"Альянс {alliance_name} успешно создан и вы стали его участником.",
                             reply_markup=ReplyKeyboardRemove())


# Вступление в альянс
@dp.message_handler(lambda message: message.text.lower().startswith('вступить в альянс'))
async def join_alliance(message: types.Message):
    user_id = str(message.from_user.id)
    player = data['players'].get(user_id)

    if not player:
        await message.answer("Вы не зарегистрированы в игре. Напишите 'Создать страну' или 'Выбрать страну'.")
        return

    alliance_name = message.text[len('вступить в альянс '):].strip()

    if alliance_name not in data['alliances']:
        await message.answer(f"Альянс {alliance_name} не существует.")
        return

    if 'alliance' in player:
        await message.answer("Вы уже состоите в альянсе.")
        return

    data['alliances'][alliance_name].append(user_id)
    player['alliance'] = alliance_name
    save_data()
    await message.answer(f"Вы успешно вступили в альянс {alliance_name}.", reply_markup=ReplyKeyboardRemove())


# Информация о альянсе
@dp.message_handler(lambda message: message.text.lower() == 'информация об альянсе')
async def alliance_info(message: types.Message):
    user_id = str(message.from_user.id)
    player = data['players'].get(user_id)

    if not player or 'alliance' not in player:
        await message.answer("Вы не состоите в альянсе. Напишите 'Создать альянс' или 'Вступить в альянс'.")
        return

    alliance_name = player['alliance']
    alliance_members = [data['players'][member]['country'] for member in data['alliances'][alliance_name]]
    alliance_info = f"Альянс: {alliance_name}\nЧлены альянса: {', '.join(alliance_members)}"

    await message.answer(alliance_info)

# Команда помощь
@dp.message_handler(lambda message: message.text.lower() == 'помощь')
async def help_command(message: types.Message):
    help_text = (
        "Доступные команды:\n"
        "/start - Начать игру\n\n"
        "Выбрать страну - Выбрать страну из доступных\n"
        "Создать страну - Создать свою страну\n\n"
        "Прокачать страну - Улучшить страну за деньги\n"
        "Мя - Получить информацию о своей стране\n"
        "Война с <страна> - Объявить войну другой стране\n\n"
        "Альянс с <страна> - Создать альянс с другой страной\n"
        "Разорвать альянс с <страна> - Разорвать альянс с другой страной\n\n"
        "Помощь - Показать список команд"
    )

    await message.answer(help_text)

# Война
@dp.message_handler(lambda message: message.text.lower().startswith('война с'))
async def declare_war(message: types.Message):
    target_country = message.text[7:].strip()
    user_id = str(message.from_user.id)
    player = data['players'].get(user_id)

    if not player:
        await message.answer("Вы не зарегистрированы в игре. Напишите 'Создать страну' или 'Выбрать страну'.")
        return

    if target_country not in data['countries'] or data['countries'][target_country] == user_id:
        await message.answer(f"Страна {target_country} не существует или это ваша страна. Попробуйте снова.")
        return

    opponent_id = data['countries'][target_country]
    opponent = data['players'].get(opponent_id)

    if not opponent:
        await message.answer("Произошла ошибка при поиске соперника. Попробуйте позже.")
        return

    player_power = player['army_level'] + random.randint(1, 10)
    opponent_power = opponent['army_level'] + random.randint(1, 10)

    if player_power > opponent_power:
        reward = opponent['budget'] * 0.1
        player['budget'] += reward
        opponent['budget'] -= reward
        result = f"Вы победили! Вы захватили {reward} долларов у {target_country}."
    else:
        penalty = player['budget'] * 0.1
        player['budget'] -= penalty
        opponent['budget'] += penalty
        result = f"Вы проиграли! Вы потеряли {penalty} долларов в пользу {target_country}."

    save_data()
    await message.answer(result)

# Обработчик кнопки "Назад"
@dp.message_handler(lambda message: message.text.lower() == 'назад')
async def go_back(message: types.Message):
    await message.answer("Вы вернулись в главное меню.", reply_markup=ReplyKeyboardRemove())

# Инициализация игры и запуск
async def on_start():
    await dp.start_polling()

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.create_task(passive_income())
    loop.run_until_complete(on_start())