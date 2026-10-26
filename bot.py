
import os
import json
import random
import telebot
from telebot import types

TOKEN = os.getenv("8709400452:AAEdn6Czd1qZ5v9boPOVOm8ALyMTzTIQAeE")
if not TOKEN:
    raise RuntimeError("BOT_TOKEN sozlanmagan!")

ADMIN_ID = 8881426607
CHANNEL = "@DrayVox_Chanel"
CHANNEL_LINK = "https://t.me/DrayVox_Chanel"
DB = "data.json"

bot = telebot.TeleBot("8709400452:AAEdn6Czd1qZ5v9boPOVOm8ALyMTzTIQAeE", parse_mode="HTML")


def load_data():
    if not os.path.exists(DB):
        return {
            "users": {},
            "contest": False,
            "winners": [],
            "prize": "Sovrin"
        }
    try:
        with open(DB, "r", encoding="utf-8") as f:
            data = json.load(f)
        data.setdefault("users", {})
        data.setdefault("contest", False)
        data.setdefault("winners", [])
        data.setdefault("prize", "Sovrin")
        return data
    except (json.JSONDecodeError, OSError):
        return {
            "users": {},
            "contest": False,
            "winners": [],
            "prize": "Sovrin"
        }


def save_data():
    with open(DB, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


data = load_data()


def is_admin(user_id):
    return user_id == ADMIN_ID


def main_menu(user_id):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("🎁 Qatnashish", "🏆 G‘oliblar")
    kb.row("📊 Statistika", "ℹ️ Yordam")
    if is_admin(user_id):
        kb.row("⚙️ Admin panel")
    return kb


def admin_menu():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("➕ Tanlov ochish", "⏹ Tanlovni tugatish")
    kb.row("👥 Qatnashchilar", "🏆 G‘olibni tanlash")
    kb.row("📊 Statistika", "🔙 Asosiy menyu")
    return kb


def subscribed(user_id):
    try:
        member = bot.get_chat_member(CHANNEL, user_id)
        return member.status in ("member", "administrator", "creator")
    except Exception:
        return False


def add_user(user):
    uid = str(user.id)
    data["users"].setdefault(uid, {
        "name": user.first_name or "Ismsiz",
        "username": user.username or "",
        "joined": False
    })
    data["users"][uid]["name"] = user.first_name or "Ismsiz"
    data["users"][uid]["username"] = user.username or ""
    save_data()


@bot.message_handler(commands=["start"])
def start(message):
    add_user(message.from_user)
    bot.send_message(
        message.chat.id,
        "🎁 <b>DRAYVOX GIVEAWAY</b>\n\n"
        "Tanlovlarda qatnashing va omadni sinab ko‘ring!",
        reply_markup=main_menu(message.from_user.id)
    )


@bot.message_handler(commands=["id"])
def show_id(message):
    bot.reply_to(message, f"Sizning Telegram ID raqamingiz: <code>{message.from_user.id}</code>")


@bot.message_handler(func=lambda m: m.text == "⚙️ Admin panel")
def open_admin(message):
    if not is_admin(message.from_user.id):
        return
    bot.send_message(message.chat.id, "⚙️ Admin panel", reply_markup=admin_menu())


@bot.message_handler(func=lambda m: m.text == "➕ Tanlov ochish")
def open_contest(message):
    if not is_admin(message.from_user.id):
        return
    data["contest"] = True
    for user in data["users"].values():
        user["joined"] = False
    save_data()
    bot.send_message(message.chat.id, "✅ Tanlov ochildi!", reply_markup=admin_menu())


@bot.message_handler(func=lambda m: m.text == "⏹ Tanlovni tugatish")
def close_contest(message):
    if not is_admin(message.from_user.id):
        return
    data["contest"] = False
    save_data()
    bot.send_message(message.chat.id, "⏹ Tanlov tugatildi.", reply_markup=admin_menu())


@bot.message_handler(func=lambda m: m.text == "🎁 Qatnashish")
def join_contest(message):
    user = message.from_user
    add_user(user)

    if not data["contest"]:
        bot.send_message(message.chat.id, "Hozircha faol tanlov yo‘q.")
        return

    if not subscribed(user.id):
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton("📢 Kanalga obuna bo‘lish", url=CHANNEL_LINK))
        kb.add(types.InlineKeyboardButton("✅ Obunani tekshirish", callback_data="check_sub"))
        bot.send_message(
            message.chat.id,
            "Tanlovda qatnashish uchun avval kanalga obuna bo‘ling.",
            reply_markup=kb
        )
        return

    uid = str(user.id)
    if data["users"][uid]["joined"]:
        bot.send_message(message.chat.id, "Siz tanlovda allaqachon qatnashyapsiz!")
        return

    data["users"][uid]["joined"] = True
    save_data()
    bot.send_message(message.chat.id, "🎉 Siz tanlovda muvaffaqiyatli qatnashyapsiz!")


@bot.callback_query_handler(func=lambda call: call.data == "check_sub")
def check_sub(call):
    user = call.from_user
    if not data["contest"]:
        bot.answer_callback_query(call.id, "Hozir faol tanlov yo‘q.")
        return

    if not subscribed(user.id):
        bot.answer_callback_query(call.id, "Avval kanalga obuna bo‘ling!", show_alert=True)
        return

    add_user(user)
    uid = str(user.id)
    if data["users"][uid]["joined"]:
        bot.answer_callback_query(call.id, "Siz allaqachon qatnashyapsiz!")
        return

    data["users"][uid]["joined"] = True
    save_data()
    bot.answer_callback_query(call.id, "Muvaffaqiyatli qatnashdingiz!")
    bot.send_message(call.message.chat.id, "🎉 Siz tanlovda qatnashyapsiz!")


@bot.message_handler(func=lambda m: m.text == "🏆 G‘oliblar")
def winners(message):
    items = data["winners"]
    if not items:
        bot.send_message(message.chat.id, "Hozircha g‘oliblar e’lon qilinmagan.")
        return
    text = "🏆 <b>Oxirgi g‘oliblar:</b>\n\n"
    for item in items[-10:][::-1]:
        text += f"🎉 {item['name']} — {item['prize']}\n"
    bot.send_message(message.chat.id, text)


@bot.message_handler(func=lambda m: m.text == "📊 Statistika")
def stats(message):
    users = data["users"]
    joined = sum(1 for u in users.values() if u.get("joined"))
    bot.send_message(
        message.chat.id,
        f"📊 <b>Statistika</b>\n"
        f"👥 Bot foydalanuvchilari: {len(users)}\n"
        f"🎁 Tanlov qatnashchilari: {joined}\n"
        f"🔔 Tanlov holati: {'Faol' if data['contest'] else 'Yopiq'}"
    )


@bot.message_handler(func=lambda m: m.text == "👥 Qatnashchilar")
def participants(message):
    if not is_admin(message.from_user.id):
        return
    joined = [
        (uid, u) for uid, u in data["users"].items()
        if u.get("joined")
    ]
    if not joined:
        bot.send_message(message.chat.id, "Hozircha qatnashchilar yo‘q.")
        return
    lines = ["👥 <b>Qatnashchilar:</b>"]
    for i, (uid, u) in enumerate(joined[:100], 1):
        name = u["name"].replace("<", "").replace(">", "")
        lines.append(f"{i}. {name} — <code>{uid}</code>")
    bot.send_message(message.chat.id, "\n".join(lines))


@bot.message_handler(func=lambda m: m.text == "🏆 G‘olibni tanlash")
def choose_winner(message):
    if not is_admin(message.from_user.id):
        return
    joined = [
        (uid, u) for uid, u in data["users"].items()
        if u.get("joined")
    ]
    if not joined:
        bot.send_message(message.chat.id, "Qatnashchilar yo‘q!")
        return

    uid, winner = random.choice(joined)
    record = {
        "id": uid,
        "name": winner["name"],
        "prize": data.get("prize", "Sovrin")
    }
    data["winners"].append(record)
    data["contest"] = False
    save_data()

    bot.send_message(
        message.chat.id,
        f"🎉 <b>G‘OLIB ANIQLANDI!</b>\n\n"
        f"🏆 G‘olib: {winner['name']}\n"
        f"🆔 ID: <code>{uid}</code>\n"
        f"🎁 Sovrin: {record['prize']}",
        reply_markup=admin_menu()
    )


@bot.message_handler(func=lambda m: m.text == "ℹ️ Yordam")
def help_message(message):
    bot.send_message(
        message.chat.id,
        "🎁 <b>Qatnashish tartibi:</b>\n"
        "1. Kanalga obuna bo‘ling.\n"
        "2. 🎁 Qatnashish tugmasini bosing.\n"
        "3. Natijani 🏆 G‘oliblar bo‘limidan ko‘ring.\n\n"
        f"📢 Kanal: {CHANNEL_LINK}"
    )


@bot.message_handler(func=lambda m: m.text == "🔙 Asosiy menyu")
def back_menu(message):
    bot.send_message(
        message.chat.id,
        "Asosiy menyu",
        reply_markup=main_menu(message.from_user.id)
    )


print("DrayVox Giveaway bot ishga tushmoqda...")
bot.infinity_polling(skip_pending=True)
