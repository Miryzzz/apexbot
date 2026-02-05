import asyncio
import os
import json
import aiohttp
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import Update, ReplyKeyboardMarkup, KeyboardButton
from http.server import BaseHTTPRequestHandler

# --- 1. НАСТРОЙКИ ---
TELEGRAM_TOKEN = "8205546825:AAE_f2o4Flap-omNJK_6R61iHHZjEbbghsE"
APEX_API_KEY = "02bc8279638509d6997130e7fc25273f"

bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher()

MAP_TRANSLATION = {
    "World's Edge": "🌋 Край Света",
    "Storm Point": "⛈ Место Бури",
    "Broken Moon": "🌒 Расколотая Луна",
    "Olympus": "☁️ Олимп",
    "Kings Canyon": "🦖 Каньон Кингс",
    "District": "🏙 Район",
    "E-District": "🌃 Э-Район",
}


# --- 2. МЕНЮ ---
def get_main_menu():
    kb = [
        [KeyboardButton(text="📊 Статистика"), KeyboardButton(text="🗺 Карты")],
        [KeyboardButton(text="📰 Новости"), KeyboardButton(text="🏆 Рейтинг (RP)")],
        [KeyboardButton(text="🛒 Магазин"), KeyboardButton(text="👤 Помощь")],
    ]
    return ReplyKeyboardMarkup(
        keyboard=kb,
        resize_keyboard=True,
        input_field_placeholder="Жду никнейм или команду...",
    )


# --- 3. ФУНКЦИИ ---


@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        f"👋 **Привет, {message.from_user.first_name}!**\n\n"
        "Я — Apex Tracker Bot. Я помогу тебе найти любую информацию.\n",
        parse_mode="Markdown",
        reply_markup=get_main_menu(),
    )


# --- КНОПКИ МЕНЮ ---


@dp.message(F.text == "🗺 Карты")
async def show_maps(message: types.Message):
    url = f"https://api.mozambiquehe.re/maprotation?auth={APEX_API_KEY}&version=2"
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, timeout=5) as response:
                data = await response.json()
                current = data["battle_royale"]["current"]
                ranked = data["ranked"]["current"]

                cur_map = MAP_TRANSLATION.get(current["map"], current["map"])
                rank_map = MAP_TRANSLATION.get(ranked["map"], ranked["map"])

                text = (
                    f"🗺 **Паблик:** {cur_map}\n⏳ Смена через: `{current['remainingTimer']}`\n\n"
                    f"🏆 **Рейтинг:** {rank_map}\n⏳ Смена через: `{ranked['remainingTimer']}`"
                )
                await message.answer(text, parse_mode="Markdown")
        except:
            await message.answer("⚠️ Ошибка получения карт.")


@dp.message(F.text == "🏆 Рейтинг (RP)")
async def show_predator(message: types.Message):
    url = f"https://api.mozambiquehe.re/predator?auth={APEX_API_KEY}"
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, timeout=10) as response:
                # Читаем текст ответа, чтобы понять, что там внутри
                raw_data = await response.text()
                
                try:
                    data = json.loads(raw_data)
                except json.JSONDecodeError:
                    await message.answer("⚠️ API прислало странный ответ. Возможно, ведутся технические работы.")
                    return

                # Проверяем, нет ли ошибки в самом ответе
                if "Error" in data:
                    await message.answer(f"❌ Ошибка API: {data.get('Error')}")
                    return
                
                pc = data.get('RP', {}).get('PC', {})
                pc_val = pc.get('val', "N/A")
                masters = pc.get('totalMastersAndPreds', "N/A")
                
                text = (
                    "🎖 **Статус Predator (PC):**\n\n"
                    f"🔴 **Порог:** `{pc_val}` RP\n"
                    f"🟣 **Мастеров:** `{masters}`\n\n"
                    "_Данные от Mozambiquehe.re_"
                )
                await message.answer(text, parse_mode="Markdown")
        except Exception as e:
            await message.answer(f"⚠️ Ошибка связи: {str(e)}")


@dp.message(F.text == "📰 Новости")
async def show_news(message: types.Message):
    url = f"https://api.mozambiquehe.re/news?auth={APEX_API_KEY}"
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url) as response:
                data = await response.json()
                msg = "📰 **Свежие новости:**\n\n"
                for item in data[:3]:
                    msg += f"🔸 [{item['title']}]({item['link']})\n"
                await message.answer(
                    msg, parse_mode="Markdown", disable_web_page_preview=True
                )
        except:
            await message.answer("📭 Новостей пока нет.")


@dp.message(F.text == "🛒 Магазин")
async def show_store(message: types.Message):
    await message.answer(
        "🛒 Полный ассортимент доступен только в игре.\nПроверяй ротацию бандлов каждый вторник!"
    )


@dp.message(F.text == "👤 Помощь")
async def show_help(message: types.Message):
    await message.answer(
        "💡 **Как проверить статистику?**\nПросто отправь мне никнейм игрока (PC/Origin) в чат, и я найду его профиль."
    )


# --- 1. ОБРАБОТКА КНОПКИ В МЕНЮ ---
@dp.message(F.text == "📊 Статистика")
async def stats_help(message: types.Message):
    await message.answer(
        "Чтобы узнать статистику, введите команду и ник игрока через пробел.\n\n"
        "Пример: `/stats ImperialHal`",
        parse_mode="Markdown"
    )

# --- 2. КОМАНДА /stats ---
@dp.message(Command("stats"))
async def get_player_stats(message: types.Message):
    args = message.text.split(maxsplit=1)
    
    if len(args) < 2:
        await message.answer("❌ Введите ник! Пример: `/stats ImperialHal`")
        return

    nickname = args[1]
    msg_wait = await message.answer(f"🔎 Сканирую базу данных для **{nickname}**...")

    url = f"https://api.mozambiquehe.re/bridge?auth={APEX_API_KEY}&player={nickname}&platform=PC"
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, timeout=10) as response:
                data = await response.json()

                if "Error" in data or response.status != 200:
                    await msg_wait.edit_text("❌ Игрок не найден. Убедись, что ник верный и это PC версия.")
                    return

                # Собираем данные
                glob = data.get("global", {})
                rank = glob.get("rank", {})
                real_time = data.get("realtime", {})
                
                name = glob.get("name", nickname)
                level = glob.get("level", 0)
                rank_name = rank.get("rankName", "Unranked")
                rank_div = rank.get("rankDiv", "")
                rank_score = rank.get("rankScore", 0)
                
                # Ссылка на иконку ранга и фон легенды
                rank_icon = rank.get("rankImg")
                selected_legend = data.get("legends", {}).get("selected", {})
                legend_name = selected_legend.get("LegendName", "Unknown")
                
                status = "🟢 В игре" if real_time.get("isOnline") == 1 else "🔴 Оффлайн"

                caption = (
                    f"👤 **Легенда:** `{name}`\n"
                    f"🆙 **Уровень:** {level} | {status}\n\n"
                    f"🏆 **Ранг:** {rank_name} {rank_div}\n"
                    f"💎 **Очки (RP):** {rank_score}\n"
                    f"🎭 **Активный герой:** {legend_name}\n\n"
                    f"📈 _Статистика обновлена из API Синдиката_"
                )

                # Удаляем временное сообщение и отправляем красивое фото с текстом
                await msg_wait.delete()
                
                if rank_icon:
                    await message.answer_photo(photo=rank_icon, caption=caption, parse_mode="Markdown")
                else:
                    await message.answer(caption, parse_mode="Markdown")

        except Exception as e:
            await msg_wait.edit_text(f"⚠️ Ошибка API. Возможно, сервер перегружен.")


# --- VERCEL HANDLER ---
class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers["Content-Length"])
        post_data = self.rfile.read(content_length)
        try:
            update_dict = json.loads(post_data.decode("utf-8"))
        except:
            return

        async def process():
            async with bot.context():
                update = Update.model_validate(update_dict, context={"bot": bot})
                await dp.feed_update(bot, update)

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(process())
        loop.close()
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"ok")

    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is Online")
