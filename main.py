import asyncio
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

steps = {
    1: {'face': 90, 'back': 90, 'left': 60, 'right': 60, 'shade': 180},
    2: {'face': 120, 'back': 120, 'left': 90, 'right': 90, 'shade': 240},
    3: {'face': 150, 'back': 150, 'left': 120, 'right': 120, 'shade': 300},
    4: {'face': 180, 'back': 180, 'left': 150, 'right': 150, 'shade': 360},
    5: {'face': 210, 'back': 210, 'left': 180, 'right': 180, 'shade': 420},
    6: {'face': 240, 'back': 240, 'left': 210, 'right': 210, 'shade': 480},
    7: {'face': 270, 'back': 270, 'left': 240, 'right': 240, 'shade': 540},
    8: {'face': 300, 'back': 300, 'left': 270, 'right': 270, 'shade': 600},
    9: {'face': 330, 'back': 330, 'left': 300, 'right': 300, 'shade': 660},
    10: {'face': 360, 'back': 360, 'left': 330, 'right': 330, 'shade': 720},
    11: {'face': 390, 'back': 390, 'left': 360, 'right': 360, 'shade': 780},
    12: {'face': 420, 'back': 420, 'left': 390, 'right': 390, 'shade': 840},
}

positions = ['face', 'back', 'left', 'right', 'shade']
position_labels = {
    'face': 'Лицом вверх',
    'back': 'На животе',
    'left': 'Левый бок',
    'right': 'Правый бок',
    'shade': 'В тени'
}
user_data = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_data[chat_id] = {'step': None, 'paused': False, 'remaining': 0, 'current_position': None}
    await context.bot.send_message(chat_id=chat_id, text="Привет, солнце! ☀️\nПодпишись на @sunxstyle и выбери шаг.")
    await context.bot.send_message(chat_id=chat_id, text="Подписался(ась)?", reply_markup=ReplyKeyboardMarkup(
        [[KeyboardButton("Да, я подписан(а)")]], resize_keyboard=True))

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    text = update.message.text
    if chat_id not in user_data:
        user_data[chat_id] = {'step': None, 'paused': False, 'remaining': 0, 'current_position': None}

    if text == "Да, я подписан(а)":
        buttons = [[str(i) for i in range(1, 5)], [str(i) for i in range(5, 9)], [str(i) for i in range(9, 13)]]
        await context.bot.send_message(chat_id=chat_id, text="Выбери шаг:", reply_markup=ReplyKeyboardMarkup(buttons, resize_keyboard=True))
        return

    if text == "Продолжить":
        if user_data[chat_id]['step'] is not None and user_data[chat_id]['step'] < 12:
            user_data[chat_id]['step'] += 1
            await start_step(chat_id, context)
        else:
            await context.bot.send_message(chat_id=chat_id, text="Это был последний шаг.")
        return

    if text == "Назад на 2 шага":
        if user_data[chat_id]['step'] is not None:
            user_data[chat_id]['step'] = max(1, user_data[chat_id]['step'] - 2)
            await start_step(chat_id, context)
        return

    if text == "Выбрать шаг":
        buttons = [[str(i) for i in range(1, 5)], [str(i) for i in range(5, 9)], [str(i) for i in range(9, 13)]]
        await context.bot.send_message(chat_id=chat_id, text="Выбери шаг:", reply_markup=ReplyKeyboardMarkup(buttons, resize_keyboard=True))
        return

    if text.isdigit():
        step = int(text)
        if step in steps:
            user_data[chat_id]['step'] = step
            await context.bot.send_message(chat_id=chat_id, text=f"Начинаем шаг {step}!")
            await start_step(chat_id, context)
        else:
            await context.bot.send_message(chat_id=chat_id, text="Шаг не найден. Введите от 1 до 12.")

async def start_step(chat_id, context):
    step = user_data[chat_id]['step']
    durations = steps[step]

    for key in positions:
        label = position_labels[key]
        duration = durations[key]
        user_data[chat_id]['remaining'] = duration
        user_data[chat_id]['paused'] = False
        user_data[chat_id]['current_position'] = key
        await context.bot.send_message(chat_id=chat_id, text=f"{label} — {duration // 60} мин")
        await run_timer(chat_id, context, duration)

    user_data[chat_id]['current_position'] = None
    await context.bot.send_message(chat_id=chat_id, text="Шаг завершён! Что дальше?", reply_markup=ReplyKeyboardMarkup(
        [["Продолжить"], ["Назад на 2 шага"], ["Выбрать шаг"]], resize_keyboard=True))

async def run_timer(chat_id, context, duration):
    while duration > 0:
        if user_data[chat_id]['paused']:
            user_data[chat_id]['remaining'] = duration
            return
        await asyncio.sleep(1)
        duration -= 1
    user_data[chat_id]['remaining'] = 0

async def pause(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_data[chat_id]['paused'] = True
    await context.bot.send_message(chat_id=chat_id, text="⏸️ Пауза.")

async def resume(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if user_data[chat_id].get('remaining', 0) > 0 and user_data[chat_id].get('current_position'):
        label = position_labels[user_data[chat_id]['current_position']]
        await context.bot.send_message(chat_id=chat_id, text=f"▶️ Возобновляем: {label} — осталось {user_data[chat_id]['remaining'] // 60} мин")
        user_data[chat_id]['paused'] = False
        await run_timer(chat_id, context, user_data[chat_id]['remaining'])
    else:
        await context.bot.send_message(chat_id=chat_id, text="⏯ Шаг неактивен. Выбери, как продолжить:", reply_markup=ReplyKeyboardMarkup(
            [["Продолжить"], ["Назад на 2 шага"], ["Выбрать шаг"]], resize_keyboard=True))

app = import os\napp = ApplicationBuilder().token(os.getenv("BOT_TOKEN")).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("pause", pause))
app.add_handler(CommandHandler("resume", resume))
app.add_handler(MessageHandler(filters.TEXT, handle_message))
app.run_polling()