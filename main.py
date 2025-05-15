
import logging
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils import executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage

API_TOKEN = "7856116405:AAFWDJM4yfMydjmnI7m-iYnTdEEbcnq9d9Y"
CHANNEL_USERNAME = "@sunxstyle"

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())

user_states = {}
timing_table = {
    1: [90, 90, 60, 60, 180],
    2: [120, 120, 60, 60, 180],
    3: [180, 180, 90, 90, 300],
    4: [300, 300, 150, 150, 300],
    5: [420, 420, 180, 180, 360],
    6: [540, 540, 240, 240, 420],
    7: [600, 600, 300, 300, 480],
    8: [600, 600, 300, 300, 600],
    9: [900, 900, 300, 300, 600],
    10: [1200, 1200, 600, 600, 600],
    11: [1500, 1500, 600, 600, 600],
    12: [1800, 1800, 600, 600, 1200],
}

positions = ["Лицом вверх", "На животе", "Левый бок", "Правый бок", "В тени"]

def steps_keyboard():
    markup = InlineKeyboardMarkup(row_width=3)
    buttons = []
    for step, times in timing_table.items():
        total = sum(times)
        minutes = total // 60
        h, m = divmod(minutes, 60)
        if h:
            label = f"{step} ({h} ч {m} мин)" if m else f"{step} ({h} ч)"
        else:
            label = f"{step} ({m} мин)"
        buttons.append(InlineKeyboardButton(label, callback_data=f"step_{step}"))
    markup.add(*buttons)
    return markup

def check_subscribed(member):
    return member.status in ("creator", "administrator", "member")

@dp.message_handler(commands=["start"])
async def send_welcome(message: types.Message):
    user_id = message.from_user.id
    member = await bot.get_chat_member(chat_id=CHANNEL_USERNAME, user_id=user_id)
    if not check_subscribed(member):
        kb = InlineKeyboardMarkup().add(InlineKeyboardButton("✅ Я подписан(а)", callback_data="check_sub"))
        await message.answer("Чтобы пользоваться ботом, подпишись на наш канал: @sunxstyle", reply_markup=kb)
        return
    user_states[user_id] = {"step": None, "position_index": 0}
    await message.answer("Привет, солнце! ☀️", reply_markup=steps_keyboard())

@dp.callback_query_handler(lambda c: c.data == "check_sub")
async def process_check_sub(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    member = await bot.get_chat_member(chat_id=CHANNEL_USERNAME, user_id=user_id)
    if check_subscribed(member):
        await callback_query.message.answer("Спасибо за подписку!", reply_markup=steps_keyboard())
    else:
        await callback_query.answer("Подпишись, чтобы пользоваться ботом!", show_alert=True)

@dp.callback_query_handler(lambda c: c.data.startswith("step_"))
async def process_step(callback_query: types.CallbackQuery):
    step = int(callback_query.data.split("_")[1])
    user_id = callback_query.from_user.id
    user_states[user_id] = {"step": step, "position_index": 0}
    await start_position(callback_query.message, user_id)

async def start_position(message, user_id):
    state = user_states[user_id]
    step = state["step"]
    pos_idx = state["position_index"]
    if pos_idx >= len(positions):
        await message.answer("Шаг завершён!", reply_markup=end_step_keyboard())
        return
    duration = timing_table[step][pos_idx]
    pos = positions[pos_idx]
    await message.answer(f"{pos} — {duration // 60} мин", reply_markup=step_controls())
    state["task"] = asyncio.create_task(position_timer(message, user_id, step, duration))

async def position_timer(message, user_id, step, duration):
    await asyncio.sleep(duration)
    if user_id in user_states and user_states[user_id].get("step") == step:
        user_states[user_id]["position_index"] += 1
        await start_position(message, user_id)

def step_controls():
    return InlineKeyboardMarkup(row_width=1).add(
        InlineKeyboardButton("⏭️ Пропустить", callback_data="skip"),
        InlineKeyboardButton("📋 Вернуться к шагам", callback_data="back_to_steps"),
        InlineKeyboardButton("↩️ Назад на 2 шага (если был перерыв)", callback_data="back_two_steps"),
        InlineKeyboardButton("⛔ Завершить", callback_data="end_session")
    )

def end_step_keyboard():
    return InlineKeyboardMarkup(row_width=1).add(
        InlineKeyboardButton("▶️ Продолжить", callback_data="continue"),
        InlineKeyboardButton("📋 Вернуться к шагам", callback_data="back_to_steps"),
        InlineKeyboardButton("↩️ Назад на 2 шага (если был перерыв)", callback_data="back_two_steps"),
        InlineKeyboardButton("⛔ Завершить", callback_data="end_session")
    )

@dp.callback_query_handler(lambda c: c.data in ["skip", "back_to_steps", "back_two_steps", "end_session", "continue"])
async def handle_controls(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    data = callback_query.data
    state = user_states.get(user_id)
    if state and "task" in state:
        state["task"].cancel()
    if data == "skip":
        state["position_index"] += 1
        await start_position(callback_query.message, user_id)
    elif data == "back_to_steps":
        await callback_query.message.answer("Выбери шаг:", reply_markup=steps_keyboard())
    elif data == "back_two_steps":
        new_step = max(1, state["step"] - 2)
        user_states[user_id] = {"step": new_step, "position_index": 0}
        await start_position(callback_query.message, user_id)
    elif data == "end_session":
        await callback_query.message.answer("Сеанс завершён. Можешь вернуться позже и начать заново ☀️",
            reply_markup=InlineKeyboardMarkup(row_width=1).add(
                InlineKeyboardButton("📋 Вернуться к шагам", callback_data="back_to_steps"),
                InlineKeyboardButton("↩️ Назад на 2 шага (если был перерыв)", callback_data="back_two_steps")
            ))
    elif data == "continue":
        await start_position(callback_query.message, user_id)

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
