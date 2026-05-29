import asyncio
import sqlite3
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, Message, InlineKeyboardMarkup, InlineKeyboardButton

# --- الإعدادات ---
API_TOKEN = '8996450262:AAHd7WtxXSmhTCsu4CVkq2lMD4xF7D7MTdw'
ADMIN_ID = 5907573792

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# --- قاعدة البيانات ---
conn = sqlite3.connect('bot_data.db', check_same_thread=False)
cursor = conn.cursor()
cursor.execute('CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, points INTEGER DEFAULT 0)')
cursor.execute('CREATE TABLE IF NOT EXISTS channels (id TEXT PRIMARY KEY, username TEXT)')
cursor.execute('CREATE TABLE IF NOT EXISTS force_sub (channel_id TEXT PRIMARY KEY)')
cursor.execute('CREATE TABLE IF NOT EXISTS services (name TEXT PRIMARY KEY, price INTEGER, active INTEGER DEFAULT 1)')
cursor.execute('CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)')
cursor.execute('INSERT OR IGNORE INTO settings (key, value) VALUES ("welcome_msg", "مرحباً بك! اشترك بالقنوات للبدء.")')
conn.commit()

class AdminStates(StatesGroup):
    waiting_for_link = State()
    waiting_for_add_points = State()
    waiting_for_welcome_msg = State()
    waiting_for_id_to_add = State()

# --- وظائف الحماية ---
async def is_subscribed(user_id):
    cursor.execute('SELECT channel_id FROM force_sub')
    for ch in cursor.fetchall():
        try:
            member = await bot.get_chat_member(chat_id=ch[0], user_id=user_id)
            if member.status == 'left': return False
        except: return False
    return True

@dp.my_chat_member()
async def monitor_bot(event: types.ChatMemberUpdated):
    chat_id = str(event.chat.id)
    if event.new_chat_member.status in ['member', 'administrator']:
        cursor.execute('INSERT OR IGNORE INTO channels (id) VALUES (?, ?)', (chat_id, event.chat.title))
    else:
        cursor.execute('DELETE FROM channels WHERE id = ?', (chat_id,))
    conn.commit()

# --- لوحة التحكم ---
def get_admin_keyboard():
    return ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="📢 إعلان للكل"), KeyboardButton(text="📊 الإحصائيات")],
        [KeyboardButton(text="💰 إضافة نقاط"), KeyboardButton(text="📝 تعديل الترحيب")],
        [KeyboardButton(text="➕ إضافة قناة اشتراك"), KeyboardButton(text="⚙️ تفعيل/تعطيل الخدمات")]
    ], resize_keyboard=True)

# --- نظام الخدمات ---
@dp.message(F.text == "🚀 طلب تمويل")
async def request_service(message: Message, state: FSMContext):
    if not await is_subscribed(message.from_user.id):
        await message.answer("⚠️ يجب الاشتراك في القنوات أولاً!")
        return
    await message.answer("أرسل رابط القناة:")
    await state.set_state(AdminStates.waiting_for_link)

@dp.callback_query(F.data.startswith("buy_"))
async def process_buy(callback: types.CallbackQuery):
    service_name = callback.data.split("_")[1]
    cursor.execute('SELECT price FROM services WHERE name = ?', (service_name,))
    price = cursor.fetchone()[0]
    cursor.execute('SELECT points FROM users WHERE id = ?', (callback.from_user.id,))
    if cursor.fetchone()[0] >= price:
        cursor.execute('UPDATE users SET points = points - ? WHERE id = ?', (price, callback.from_user.id))
        conn.commit()
        await callback.message.answer("✅ تم خصم النقاط وبدء الخدمة.")
    else:
        await callback.message.answer("❌ رصيدك غير كافٍ.")

# --- الأوامر الإدارية ---
@dp.message(Command("start"))
async def start(message: Message):
    if message.from_user.id == ADMIN_ID:
        await message.answer("أهلاً بك يا مدير:", reply_markup=get_admin_keyboard())
    else:
        cursor.execute('INSERT OR IGNORE INTO users (id) VALUES (?)', (message.from_user.id,))
        conn.commit()
        welcome = cursor.execute('SELECT value FROM settings WHERE key="welcome_msg"').fetchone()[0]
        await message.answer(welcome, reply_markup=ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="🚀 طلب تمويل")]], resize_keyboard=True))

async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
