import logging
import asyncio
from datetime import datetime
from telegram import Update
from telegram.ext import Application, MessageHandler, CommandHandler, filters, ContextTypes
from flask import Flask
import threading
import os

# ---------------- Flask (فتح Port للاستضافة) ----------------
app = Flask(__name__)

@app.route("/")
def home():
    return "Bot is alive 🚀"

def run_flask():
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port)

threading.Thread(target=run_flask).start()

# ---------------- Logging ----------------
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# ---------------- Variables ----------------
user_warnings = {}

# ---------------- Handlers ----------------
async def welcome_new_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    for new_user in update.message.new_chat_members:
        if new_user.id == context.bot.id:
            continue

        user_name = new_user.first_name
        user_id = new_user.id
        user_username = f"@{new_user.username}" if new_user.username else "-"
        current_date = datetime.now().strftime("%d/%m/%Y")

        welcome_text = f"""━━━━━━━━━━━━━━━━━━━━
اهلا بك في مجموعة GTA.SAN Andreas
━━━━━━━━━━━━━━━━━━━━
⚡️ معلومات المستخدم ⚡️
✦ الاسم : ⊀ {user_name} ⊁
✦ الايدي : ⊀ {user_id} ⊁
✦ اليوزر : ⊀ {user_username} ⊁
✦ التاريخ : ⊀ {current_date} ⊁

❗️ اتبع القوانين ❗️
➪︎ عدم ارسال روابط
➪︎ عدم دخول لاشخاص في الخاص
➪︎ عدم السب والشتم
➪ عدم ارسال 10 صور في نفس الوقت
➪ عدم البيع والشراء داخل المجموعة
⚠️ في حال اي مخالفة سيتم حظرك ❎
━━━━━━━━━━━━━━━━━━━━
"""
        await update.message.reply_text(welcome_text)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ البوت شغال تمام.")

async def handle_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_message or not update.effective_user:
        return

    message = update.effective_message
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    text = message.text or message.caption or ""

    if update.effective_chat.type == "private":
        return

    try:
        chat_member = await context.bot.get_chat_member(chat_id, user_id)
        if chat_member.status in ['administrator', 'creator']:
            return
    except:
        pass

    # --------- Link check ---------
    if message.entities:
        if any(e.type in ['url', 'text_link'] for e in message.entities):
            try:
                await message.delete()
                user_warnings[user_id] = user_warnings.get(user_id, 0) + 1

                if user_warnings[user_id] >= 2:
                    await context.bot.ban_chat_member(chat_id, user_id)
                    await context.bot.send_message(
                        chat_id,
                        f"🚫 تم حظر {update.effective_user.first_name} بسبب تكرار الروابط."
                    )
                    user_warnings[user_id] = 0
                else:
                    warn = await context.bot.send_message(
                        chat_id,
                        f"⚠️ {update.effective_user.first_name} الروابط ممنوعة!"
                    )
                    asyncio.create_task(delete_after_delay(warn, 5))
            except Exception as e:
                logging.error(e)

    # --------- Bad words ---------
    bad_words = [
        'كسم', 'شرموطة', 'لوطى', 'تعالى خاص', 'سكس', 'xxx', 'xnxx'
    ]
    if any(word in text for word in bad_words):
        try:
            await message.delete()
        except:
            pass

async def delete_after_delay(message, delay):
    await asyncio.sleep(delay)
    try:
        await message.delete()
    except:
        pass

# ---------------- Main ----------------
def main():
    TOKEN = os.getenv("BOT_TOKEN")
    if not TOKEN:
        raise ValueError("BOT_TOKEN غير موجود في Environment Variables")

    application = Application.builder().token(TOKEN).build()

    application.add_handler(
        MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome_new_member)
    )
    application.add_handler(CommandHandler("start", start))
    application.add_handler(
        MessageHandler(filters.TEXT | filters.CAPTION & ~filters.COMMAND, handle_messages)
    )

    print("🤖 Bot is running...")
    application.run_polling()

if __name__ == "__main__":
    main()
