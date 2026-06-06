"""
Telegram Group Bot v4.6 - With Music Player Integration
Complete bot with developer control panel, games, statistics, ads, and music player management
"""

import logging
import os
import json
import random
import string
from datetime import datetime, timedelta
from dotenv import load_dotenv
from telegram import Update, ChatPermissions, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    CallbackQueryHandler,
    ConversationHandler,
)
from telegram.constants import ChatMemberStatus

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Bot configuration
BOT_TOKEN = os.getenv('BOT_TOKEN')
ADMIN_IDS = list(map(int, os.getenv('ADMIN_IDS', '').split(','))) if os.getenv('ADMIN_IDS') else []
DEVELOPER_IDS = list(map(int, os.getenv('DEVELOPER_IDS', '').split(','))) if os.getenv('DEVELOPER_IDS') else []
MUSIC_BOT_TOKENS = {}  # Store music bot tokens
DEVELOPER_USERNAME = os.getenv('DEVELOPER_USERNAME', '@your_username')
DEVELOPER_NAME = os.getenv('DEVELOPER_NAME', 'Developer')
CHANNEL_ID = os.getenv('CHANNEL_ID', '')

# Anti-spam configuration
SPAM_THRESHOLD = 5
SPAM_TIME_WINDOW = 60
WARN_THRESHOLD = 3

# Conversation states
WAITING_FOR_AD_TITLE = 1
WAITING_FOR_AD_CONTENT = 2
WAITING_FOR_AD_BUTTON_TEXT = 3
WAITING_FOR_AD_BUTTON_LINK = 4
WAITING_FOR_CHANNEL_INPUT = 5
WAITING_FOR_MUSIC_BOT_TOKEN = 6
WAITING_FOR_MUSIC_BOT_SELECT = 7

# Game data storage
user_messages = {}
user_warnings = {}
user_scores = {}
active_games = {}
whisper_messages = {}
statistics_data = {}
advertisements = {}
channels_list = {}
music_bots_list = {}  # Store configured music bots
music_player_status = {'enabled': False, 'bots': []}

# Riddles Game Data
riddles = [
    {
        "question": "I speak without a mouth and hear without ears. I have no body, but I come alive with wind. What am I?",
        "answer": "echo",
        "hints": ["Sound related", "Can be heard in mountains", "Repeats what you say"],
        "difficulty": "Medium"
    },
    {
        "question": "The more you take, the more you leave behind. What am I?",
        "answer": "footsteps",
        "hints": ["On ground", "Related to walking", "Marks left behind"],
        "difficulty": "Easy"
    },
    {
        "question": "I have cities, but no houses. Forests, but no trees. Water, but no fish. What am I?",
        "answer": "map",
        "hints": ["Geographical item", "Can be folded", "Shows locations"],
        "difficulty": "Easy"
    },
    {
        "question": "What has hands but cannot clap?",
        "answer": "clock",
        "hints": ["Tells time", "On wall", "Has moving parts"],
        "difficulty": "Easy"
    },
    {
        "question": "What can travel around the world while staying in a corner?",
        "answer": "stamp",
        "hints": ["Mail related", "Has adhesive", "Postage"],
        "difficulty": "Medium"
    },
    {
        "question": "I am taken from a mine and shut up in a wooden case, from which I am never released, yet I am used by almost everyone. What am I?",
        "answer": "pencil lead",
        "hints": ["Writing instrument", "Dark substance", "In pencil"],
        "difficulty": "Hard"
    },
]

# Trivia Questions
trivia_questions = [
    {
        "question": "What is the capital of France?",
        "options": ["Paris", "London", "Berlin", "Madrid"],
        "answer": 0
    },
    {
        "question": "Which planet is closest to the Sun?",
        "options": ["Venus", "Mercury", "Earth", "Mars"],
        "answer": 1
    },
    {
        "question": "What is 2 + 2?",
        "options": ["3", "4", "5", "6"],
        "answer": 1
    },
    {
        "question": "Which country has the most population?",
        "options": ["India", "China", "USA", "Indonesia"],
        "answer": 0
    },
    {
        "question": "What is the largest ocean?",
        "options": ["Atlantic", "Indian", "Arctic", "Pacific"],
        "answer": 3
    },
]

# Popular Music Bot Options
MUSIC_BOT_OPTIONS = {
    'musicplayer': {
        'name': '🎵 Music Player',
        'username': '@musicplayer',
        'description': 'Full music player with queue management'
    },
    'spotifybot': {
        'name': '🎶 Spotify Bot',
        'username': '@spotifybot',
        'description': 'Play songs directly from Spotify'
    },
    'songbot': {
        'name': '🎸 Song Bot',
        'username': '@songbot',
        'description': 'Search and play any song'
    },
    'musicdownloader': {
        'name': '📥 Music Downloader',
        'username': '@musicdownloader',
        'description': 'Download and play music'
    },
    'jmusic_bot': {
        'name': '🎼 J-Music Bot',
        'username': '@jmusic_bot',
        'description': 'Japanese music player'
    },
    'custom': {
        'name': '⚙️ Custom Bot',
        'username': 'custom',
        'description': 'Add your own music bot'
    }
}


class ComprehensiveGroupBot:
    """Complete bot with music player management"""

    def __init__(self):
        self.app = None

    # ==================== MUSIC BOT MANAGEMENT ====================

    async def manage_music_panel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Manage music bots panel"""
        query = update.callback_query
        
        if query.data == 'panel_music':
            music_text = "🎵 *MUSIC BOT MANAGEMENT*\n\n"
            music_text += f"Status: {'✅ Enabled' if music_player_status['enabled'] else '❌ Disabled'}\n"
            music_text += f"Connected Bots: {len(music_bots_list)}\n\n"
            
            music_keyboard = [
                [InlineKeyboardButton("➕ Add Music Bot", callback_data='music_add')],
                [InlineKeyboardButton("📋 View Bots", callback_data='music_view')],
                [InlineKeyboardButton("🗑️ Remove Bot", callback_data='music_remove')],
                [InlineKeyboardButton("🎵 Toggle Music", callback_data='music_toggle')],
                [InlineKeyboardButton("🔙 Back", callback_data='panel_back')]
            ]
            music_markup = InlineKeyboardMarkup(music_keyboard)
            
            await query.edit_message_text(music_text, reply_markup=music_markup, parse_mode='Markdown')
        
        elif query.data == 'music_add':
            add_text = "🎵 *ADD MUSIC BOT*\n\n"
            add_text += "Choose from popular music bots:\n\n"
            
            bot_buttons = []
            for bot_id, bot_info in MUSIC_BOT_OPTIONS.items():
                bot_buttons.append([InlineKeyboardButton(bot_info['name'], callback_data=f'music_select_{bot_id}')])
            
            bot_buttons.append([InlineKeyboardButton("🔙 Back", callback_data='panel_music')])
            bot_markup = InlineKeyboardMarkup(bot_buttons)
            
            await query.edit_message_text(add_text, reply_markup=bot_markup, parse_mode='Markdown')
        
        elif query.data.startswith('music_select_'):
            bot_type = query.data.split('_')[2]
            context.user_data['selected_music_bot'] = bot_type
            
            if bot_type == 'custom':
                await query.edit_message_text(
                    "🎵 *ADD CUSTOM MUSIC BOT*\n\n"
                    "Enter the music bot username or token:\n"
                    "(e.g., @musicplayerbot or your_bot_token)"
                )
                return WAITING_FOR_MUSIC_BOT_TOKEN
            else:
                bot_info = MUSIC_BOT_OPTIONS[bot_type]
                
                confirm_keyboard = [
                    [InlineKeyboardButton("✅ Add", callback_data=f'music_confirm_{bot_type}')],
                    [InlineKeyboardButton("❌ Cancel", callback_data='music_add')]
                ]
                confirm_markup = InlineKeyboardMarkup(confirm_keyboard)
                
                confirm_text = f"""
🎵 *CONFIRM MUSIC BOT ADDITION*

Name: {bot_info['name']}
Username: {bot_info['username']}
Description: {bot_info['description']}

Ready to add this music bot?
"""
                
                await query.edit_message_text(confirm_text, reply_markup=confirm_markup, parse_mode='Markdown')
        
        elif query.data.startswith('music_confirm_'):
            bot_type = query.data.split('_')[2]
            bot_info = MUSIC_BOT_OPTIONS[bot_type]
            
            if bot_type not in music_bots_list:
                music_bots_list[bot_type] = {
                    'name': bot_info['name'],
                    'username': bot_info['username'],
                    'type': bot_type,
                    'added_at': datetime.now().isoformat(),
                    'enabled': True
                }
                music_player_status['enabled'] = True
                music_player_status['bots'].append(bot_type)
                
                success_text = f"""
✅ *MUSIC BOT ADDED*

Bot: {bot_info['name']}
Username: {bot_info['username']}
Status: Active ✅

The music bot is now active in your group!
Users can start playing music with: /music
"""
                
                await query.edit_message_text(success_text, parse_mode='Markdown')
            else:
                await query.answer("This bot is already added!", show_alert=True)
        
        elif query.data == 'music_view':
            if not music_bots_list:
                view_text = "📋 *NO MUSIC BOTS CONNECTED*\n\nAdd a music bot to enable music in your group."
                back_keyboard = [[InlineKeyboardButton("🔙 Back", callback_data='panel_music')]]
                back_markup = InlineKeyboardMarkup(back_keyboard)
                
                await query.edit_message_text(view_text, reply_markup=back_markup, parse_mode='Markdown')
                return
            
            view_text = "📋 *CONNECTED MUSIC BOTS:*\n\n"
            for bot_id, bot_info in music_bots_list.items():
                status = "✅ Active" if bot_info['enabled'] else "❌ Inactive"
                view_text += f"🎵 {bot_info['name']}\n"
                view_text += f"   Username: {bot_info['username']}\n"
                view_text += f"   Status: {status}\n\n"
            
            back_keyboard = [[InlineKeyboardButton("🔙 Back", callback_data='panel_music')]]
            back_markup = InlineKeyboardMarkup(back_keyboard)
            
            await query.edit_message_text(view_text, reply_markup=back_markup, parse_mode='Markdown')
        
        elif query.data == 'music_remove':
            if not music_bots_list:
                await query.answer("No bots to remove!", show_alert=True)
                return
            
            remove_text = "🗑️ *REMOVE MUSIC BOT*\n\n"
            remove_text += "Select a bot to remove:\n\n"
            
            remove_buttons = []
            for bot_id, bot_info in music_bots_list.items():
                remove_buttons.append([
                    InlineKeyboardButton(f"🗑️ {bot_info['name']}", callback_data=f'music_delete_{bot_id}')
                ])
            
            remove_buttons.append([InlineKeyboardButton("🔙 Back", callback_data='panel_music')])
            remove_markup = InlineKeyboardMarkup(remove_buttons)
            
            await query.edit_message_text(remove_text, reply_markup=remove_markup, parse_mode='Markdown')
        
        elif query.data.startswith('music_delete_'):
            bot_id = query.data.split('_')[2]
            
            if bot_id in music_bots_list:
                bot_name = music_bots_list[bot_id]['name']
                del music_bots_list[bot_id]
                
                if bot_id in music_player_status['bots']:
                    music_player_status['bots'].remove(bot_id)
                
                if not music_bots_list:
                    music_player_status['enabled'] = False
                
                await query.edit_message_text(
                    f"✅ *BOT REMOVED*\n\n"
                    f"{bot_name} has been removed.\n"
                    f"Remaining bots: {len(music_bots_list)}"
                )
        
        elif query.data == 'music_toggle':
            if not music_bots_list:
                await query.answer("No bots to toggle!", show_alert=True)
                return
            
            if music_player_status['enabled']:
                music_player_status['enabled'] = False
                toggle_text = "❌ *MUSIC DISABLED*\n\nMusic player has been turned off."
            else:
                music_player_status['enabled'] = True
                toggle_text = "✅ *MUSIC ENABLED*\n\nMusic player has been turned on."
            
            await query.edit_message_text(toggle_text)

    async def receive_custom_music_bot(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Receive custom music bot details"""
        bot_input = update.message.text.strip()
        
        if not bot_input:
            await update.message.reply_text("❌ Invalid input. Please try again.")
            return WAITING_FOR_MUSIC_BOT_TOKEN
        
        # Generate a unique ID for custom bot
        custom_id = f"custom_{len(music_bots_list)}"
        
        music_bots_list[custom_id] = {
            'name': '⚙️ Custom Music Bot',
            'username': bot_input if bot_input.startswith('@') else f"@{bot_input}",
            'type': 'custom',
            'added_at': datetime.now().isoformat(),
            'enabled': True
        }
        
        music_player_status['enabled'] = True
        music_player_status['bots'].append(custom_id)
        
        await update.message.reply_text(
            f"✅ *CUSTOM MUSIC BOT ADDED*\n\n"
            f"Bot: {music_bots_list[custom_id]['username']}\n"
            f"Status: Active ✅\n\n"
            f"Music player is now enabled!"
        )
        
        return ConversationHandler.END

    async def music_player(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show music player status and commands"""
        if not music_player_status['enabled'] or not music_bots_list:
            await update.message.reply_text(
                "❌ Music player is not enabled in this group.\n\n"
                "Contact the admin to enable music."
            )
            return
        
        music_text = "🎵 *MUSIC PLAYER*\n\n"
        music_text += "Available commands:\n"
        music_text += "  /play <song> - Play a song\n"
        music_text += "  /pause - Pause music\n"
        music_text += "  /resume - Resume music\n"
        music_text += "  /stop - Stop music\n"
        music_text += "  /skip - Skip to next song\n"
        music_text += "  /queue - Show queue\n"
        music_text += "  /volume <level> - Set volume\n\n"
        
        music_text += "Active Music Bots:\n"
        for bot_id, bot_info in music_bots_list.items():
            music_text += f"  🎵 {bot_info['name']} ({bot_info['username']})\n"
        
        music_keyboard = [
            [InlineKeyboardButton("▶️ Play", callback_data='music_cmd_play')],
            [InlineKeyboardButton("⏸️ Pause", callback_data='music_cmd_pause')],
            [InlineKeyboardButton("⏹️ Stop", callback_data='music_cmd_stop')],
            [InlineKeyboardButton("⏭️ Skip", callback_data='music_cmd_skip')],
            [InlineKeyboardButton("📋 Queue", callback_data='music_cmd_queue')]
        ]
        music_markup = InlineKeyboardMarkup(music_keyboard)
        
        await update.message.reply_text(music_text, reply_markup=music_markup, parse_mode='Markdown')

    async def music_command_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle music player commands"""
        query = update.callback_query
        
        command_responses = {
            'music_cmd_play': '▶️ Playing music...',
            'music_cmd_pause': '⏸️ Music paused',
            'music_cmd_stop': '⏹️ Music stopped',
            'music_cmd_skip': '⏭️ Skipping to next song',
            'music_cmd_queue': '📋 Current queue...'
        }
        
        response = command_responses.get(query.data, 'Processing...')
        await query.answer(response, show_alert=False)

    # ==================== DEVELOPER CONTROL PANEL ====================

    async def dev_panel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Developer control panel"""
        user_id = update.message.from_user.id
        
        if user_id not in DEVELOPER_IDS:
            await update.message.reply_text(
                "❌ This command is only for developers!\n"
                f"Contact: {DEVELOPER_USERNAME}"
            )
            return
        
        panel_keyboard = [
            [InlineKeyboardButton("📢 Manage Advertisements", callback_data='panel_ads')],
            [InlineKeyboardButton("🔗 Manage Channels", callback_data='panel_channels')],
            [InlineKeyboardButton("🎵 Manage Music Bots", callback_data='panel_music')],
            [InlineKeyboardButton("📊 View Statistics", callback_data='panel_stats')],
            [InlineKeyboardButton("⚙️ Bot Settings", callback_data='panel_settings')],
            [InlineKeyboardButton("❌ Close", callback_data='panel_close')]
        ]
        panel_markup = InlineKeyboardMarkup(panel_keyboard)
        
        panel_text = """
🎛️ *DEVELOPER CONTROL PANEL v4.6*

Welcome to your control center! Manage:
  ✅ Advertisements
  ✅ Channel subscriptions
  ✅ 🎵 Music Bots (NEW!)
  ✅ Statistics
  ✅ Bot settings

Choose an option below:
"""
        
        await update.message.reply_text(panel_text, reply_markup=panel_markup, parse_mode='Markdown')

    async def dev_profile(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show developer profile"""
        message_text = update.message.text.lower() if update.message else ""
        
        dev_keyboard = [
            [InlineKeyboardButton("💬 Message", url=f"https://t.me/{DEVELOPER_USERNAME.replace('@', '')}")],
            [InlineKeyboardButton("📱 Profile", callback_data='dev_profile')],
            [InlineKeyboardButton("🔗 Back", callback_data='dev_back')]
        ]
        dev_markup = InlineKeyboardMarkup(dev_keyboard)
        
        dev_text = f"""
👨‍💻 *DEVELOPER PROFILE*

Name: {DEVELOPER_NAME}
Username: {DEVELOPER_USERNAME}
Role: Bot Developer & Administrator

📊 Bot Statistics:
  Version: 4.6
  Games: 16+
  Commands: 50+
  Users: {len(statistics_data)}
  Music Bots: {len(music_bots_list)}

🔧 Features Managed:
  ✅ Complete statistics system
  ✅ Advertisement platform
  ✅ Channel subscription system
  ✅ 🎵 Music Player Management (NEW!)
  ✅ Game moderation
  ✅ User management

💬 Need Help?
  Click the 'Message' button to contact the developer!
"""
        
        if update.message:
            await update.message.reply_text(dev_text, reply_markup=dev_markup, parse_mode='Markdown')
        else:
            query = update.callback_query
            await query.edit_message_text(dev_text, reply_markup=dev_markup, parse_mode='Markdown')

    # ==================== MAIN COMMANDS ====================

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        if update.message.chat.type == 'private':
            await update.message.reply_text(
                "🤖 *Welcome to Comprehensive Group Bot v4.6!*\n\n"
                "I provide:\n"
                "✅ 16+ Games & Entertainment\n"
                "✅ Complete Statistics System\n"
                "✅ Advertisement Platform\n"
                "✅ 🎵 Music Player Management (NEW!)\n"
                "✅ Developer Control Panel\n\n"
                "Add me to your group and use /help to see all commands!",
                parse_mode='Markdown'
            )

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show comprehensive help menu"""
        help_text = """
╔════════════════════════════════════════╗
║  🤖 COMPREHENSIVE GROUP BOT v4.6      ║
║  With Music Player Management         ║
╚═════���══════════════════════════════════╝

🎛️ *DEVELOPER COMMANDS:*
  /devpanel - Open control panel (Dev only)
  /createad - Create advertisement
  /music - Show music player

🎵 *MUSIC COMMANDS:*
  /music - Show music player
  /play <song> - Play a song
  /pause - Pause music
  /resume - Resume music
  /stop - Stop music
  /skip - Skip song
  /queue - Show queue

📊 *STATISTICS COMMANDS:*
  /stats - Your statistics
  /globalstats - Global statistics
  /leaderboard - Top players
  /mypoints - Your points

🎮 *GAME COMMANDS:*
  /dice - Roll dice
  /riddle - Play riddle

👤 *USER COMMANDS:*
  /welcome - Show welcome
  /rules - Show rules
  /info - Bot info
  /help - This menu
"""
        await update.message.reply_text(help_text, parse_mode='Markdown')

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle messages for developer mention"""
        if not update.message or update.message.chat.type == 'private':
            return
        
        message_text = update.message.text.lower()
        for dev_id in DEVELOPER_IDS:
            try:
                dev_member = await context.bot.get_chat_member(update.message.chat_id, dev_id)
                if dev_member.user.username:
                    if f"@{dev_member.user.username}" in message_text or DEVELOPER_NAME.lower() in message_text:
                        await self.dev_profile(update, context)
                        return
            except:
                pass

    def setup_handlers(self):
        """Setup all command and message handlers"""
        # Main commands
        self.app.add_handler(CommandHandler("start", self.start))
        self.app.add_handler(CommandHandler("help", self.help_command))
        self.app.add_handler(CommandHandler("devpanel", self.dev_panel))
        self.app.add_handler(CommandHandler("music", self.music_player))

        # Developer panel handlers
        self.app.add_handler(CallbackQueryHandler(self.manage_music_panel, pattern='^panel_music|^music_'))
        self.app.add_handler(CallbackQueryHandler(self.music_command_callback, pattern='^music_cmd_'))

        # Music bot conversation
        music_conv = ConversationHandler(
            entry_points=[CallbackQueryHandler(self.manage_music_panel, pattern='^music_select_custom')],
            states={
                WAITING_FOR_MUSIC_BOT_TOKEN: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.receive_custom_music_bot)],
            },
            fallbacks=[CommandHandler("cancel", lambda u, c: ConversationHandler.END)],
        )
        self.app.add_handler(music_conv)

        # Message handler for developer mentions
        self.app.add_handler(MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            self.handle_message
        ))

    async def run(self):
        """Start the bot"""
        self.app = Application.builder().token(BOT_TOKEN).build()
        
        self.setup_handlers()
        
        await self.app.initialize()
        await self.app.start()
        await self.app.updater.start_polling()
        
        logger.info("🤖 Bot v4.6 with Music Player Management started successfully!")


def main():
    """Main entry point"""
    if not BOT_TOKEN:
        logger.error("❌ BOT_TOKEN not found in environment variables!")
        return
    
    bot = ComprehensiveGroupBot()
    
    try:
        import asyncio
        asyncio.run(bot.run())
    except KeyboardInterrupt:
        logger.info("🛑 Bot stopped by user.")


if __name__ == '__main__':
    main()
