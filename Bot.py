# import asyncio
# import os
# import re
# from datetime import datetime, timedelta

# from telethon import TelegramClient, events, Button


# # ===== НАСТРОЙКИ =====
# api_id = int(os.getenv("API_ID", "31387061"))
# api_hash = os.getenv("API_HASH", "faf65d39b730173230826188e50e761e")
# PHONE = os.getenv("PHONE", "+79932463918")

# SESSION_NAME = "user_session"


# # ===== ВСПОМОГАТЕЛЬНОЕ =====

# def extract_username(link: str):
#     match = re.search(r"t\.me/([a-zA-Z0-9_]+)", link)
#     return match.group(1) if match else None


# def calc_score(msg):
#     views = msg.views or 0
#     reactions = 0
#     if msg.reactions and msg.reactions.results:
#         for r in msg.reactions.results:
#             reactions += r.count
#     score = views + reactions * 5
#     return score, views, reactions


# def parse_date(date_str: str):
#     try:
#         return datetime.strptime(date_str.strip(), "%d.%m.%Y")
#     except ValueError:
#         return None


# def delete_session_files():
#     """Удаляет файлы сессии для принудительной повторной авторизации"""
#     files_to_delete = [
#         f"{SESSION_NAME}.session",
#         f"{SESSION_NAME}.session-journal"
#     ]
#     deleted = []
#     for file in files_to_delete:
#         if os.path.exists(file):
#             try:
#                 os.remove(file)
#                 deleted.append(file)
#             except Exception as e:
#                 print(f"⚠️ Не удалось удалить {file}: {e}")
#     if deleted:
#         print(f"🗑️ Удалены файлы сессии: {', '.join(deleted)}")
#     else:
#         print("ℹ️ Файлов сессии не найдено")


# async def get_top_post_period(client, channel_link: str, start_date: datetime, end_date: datetime):
#     """Получает самый популярный пост за произвольный период"""
#     username = extract_username(channel_link)
#     if not username:
#         return None, "❌ Неверная ссылка. Пример: https://t.me/durov"

#     try:
#         channel = await client.get_entity(username)
#     except Exception as e:
#         return None, f"❌ Канал @{username} не найден.\nОшибка: {e}"

#     if start_date > end_date:
#         return None, "❌ Дата начала не может быть позже даты конца"
#     if end_date > datetime.utcnow():
#         return None, "❌ Дата конца не может быть в будущем"

#     messages = await client.get_messages(channel, limit=300)

#     best = None
#     best_score = 0
#     stats = None

#     for msg in messages:
#         msg_date = msg.date.replace(tzinfo=None) if msg.date.tzinfo else msg.date
#         if msg_date < start_date or msg_date > end_date:
#             continue

#         score, views, reactions = calc_score(msg)
#         if score > best_score:
#             best_score = score
#             best = msg
#             stats = (views, reactions)

#     if not best:
#         start_str = start_date.strftime("%d.%m.%Y")
#         end_str = end_date.strftime("%d.%m.%Y")
#         return None, f"📭 Нет постов с {start_str} по {end_str}"

#     views, reactions = stats
#     post_link = f"https://t.me/{username}/{best.id}"
#     start_str = start_date.strftime("%d.%m.%Y")
#     end_str = end_date.strftime("%d.%m.%Y")

#     text = (
#         f"🔥 <b>Самый популярный пост</b>\n\n"
#         f"📢 Канал: @{username}\n"
#         f"📅 Период: <b>{start_str} — {end_str}</b>\n\n"
#         f"👁 Просмотры: <b>{views:,}</b>\n"
#         f"❤️ Реакции: <b>{reactions:,}</b>\n"
#         f"⭐ Рейтинг: <b>{best_score:,}</b>\n\n"
#         f"🔗 {post_link}"
#     )

#     return post_link, text


# # ===== ХЕНДЛЕРЫ (определяются позже, после создания client) =====

# def setup_handlers(client):
#     """Регистрирует все хендлеры после создания клиента"""

#     @client.on(events.NewMessage(pattern='/start'))
#     async def start(event):
#         await event.respond(
#             "👋 <b>Привет!</b>\n\n"
#             "Отправь ссылку на канал и период в формате:\n"
#             "<code>https://t.me/durov 01.01.2024-15.01.2024</code>\n\n"
#             "Где:\n"
#             "• <code>01.01.2024</code> — начало периода\n"
#             "• <code>15.01.2024</code> — конец периода\n\n"
#             "📌 Также можно указать только дни:\n"
#             "<code>https://t.me/durov 7</code> — за последние 7 дней",
#             parse_mode='html'
#         )

#     @client.on(events.NewMessage)
#     async def handler(event):
#         text = event.text.strip()

#         if text.startswith('/') or "t.me/" not in text:
#             return

#         parts = text.split()
#         link = parts[0]

#         username = extract_username(link)
#         if not username:
#             await event.respond("❌ Неверная ссылка. Пример: https://t.me/durov", parse_mode='html')
#             return

#         start_date = None
#         end_date = None

#         if len(parts) > 1:
#             period_str = parts[1]

#             if "-" in period_str and "." in period_str:
#                 date_parts = period_str.split("-")
#                 if len(date_parts) == 2:
#                     start_date = parse_date(date_parts[0])
#                     end_date = parse_date(date_parts[1])

#                     if not start_date or not end_date:
#                         await event.respond(
#                             "❌ Неверный формат дат.\n"
#                             "Используйте: <code>01.01.2024-15.01.2024</code>",
#                             parse_mode='html'
#                         )
#                         return

#             elif period_str.isdigit():
#                 days = int(period_str)
#                 if days < 1 or days > 365:
#                     await event.respond("❌ Укажите от 1 до 365 дней", parse_mode='html')
#                     return
#                 end_date = datetime.utcnow()
#                 start_date = end_date - timedelta(days=days)

#         if start_date is None or end_date is None:
#             end_date = datetime.utcnow()
#             start_date = end_date - timedelta(days=7)

#         start_str = start_date.strftime("%d.%m.%Y")
#         end_str = end_date.strftime("%d.%m.%Y")
#         await event.respond(
#             f"⏳ <b>Анализирую посты...</b>\n"
#             f"Период: {start_str} — {end_str}\n\n"
#             f"Пожалуйста, подождите.",
#             parse_mode='html'
#         )

#         post_link, result = await get_top_post_period(client, link, start_date, end_date)

#         if post_link:
#             await event.respond(
#                 result,
#                 buttons=[[Button.url("🔗 Открыть пост", post_link)]],
#                 parse_mode='html',
#                 link_preview=False
#             )
#         else:
#             await event.respond(result, parse_mode='html')


# # ===== ЗАПУСК =====

# async def main():
#     print("🗑️ Очистка старой сессии...")
#     delete_session_files()

#     print("🔐 Требуется авторизация...")
#     print(f"📱 Номер для входа: {PHONE}")
#     print("-" * 40)

#     # ✅ Создаём клиент ПЕРЕД регистрацией хендлеров
#     client = TelegramClient(SESSION_NAME, api_id, api_hash)

#     # ✅ Регистрируем хендлеры после создания client
#     setup_handlers(client)

#     await client.start(phone=PHONE)

#     print("-" * 40)
#     print("✅ Авторизация успешна! Бот работает.")
#     print("📅 Формат: https://t.me/channel дд.мм.гггг-дд.мм.гггг")
#     print("🛑 Нажмите Ctrl+C для выхода")

#     await client.run_until_disconnected()


# if __name__ == "__main__":
#     asyncio.run(main())

print('гойда')