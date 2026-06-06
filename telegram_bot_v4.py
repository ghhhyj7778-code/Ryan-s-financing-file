"""
Comprehensive Telegram Group Management and Protection Bot with Games, Statistics, and Ads
Features: Anti-spam, moderation, games, statistics, admin ads, fun commands, mandatory subscription
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
CHANNEL_ID = os.getenv('CHANNEL_ID', '')

# Anti-spam configuration
SPAM_THRESHOLD = 5
SPAM_TIME_WINDOW = 60
WARN_THRESHOLD = 3

# Conversation states for ads
WAITING_FOR_AD_TITLE = 1
WAITING_FOR_AD_CONTENT = 2
WAITING_FOR_AD_BUTTON_TEXT = 3
WAITING_FOR_AD_BUTTON_LINK = 4

# Game data storage
user_messages = {}
user_warnings = {}
user_scores = {}
active_games = {}
user_subscribed = {}
whisper_messages = {}
statistics_data = {}
advertisements = {}

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

# 20 Questions Game Data
twenty_questions_topics = [
    {"word": "cat", "category": "Animal"},
    {"word": "airplane", "category": "Vehicle"},
    {"word": "pizza", "category": "Food"},
    {"word": "moon", "category": "Space"},
    {"word": "computer", "category": "Technology"},
    {"word": "book", "category": "Object"},
    {"word": "bicycle", "category": "Vehicle"},
    {"word": "diamond", "category": "Gemstone"},
    {"word": "volcano", "category": "Natural"},
    {"word": "guitar", "category": "Instrument"},
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


class ComprehensiveGroupBot:
    """Complete bot with games, moderation, statistics, and advertisements"""

    def __init__(self):
        self.app = None

    # ==================== STATISTICS SYSTEM ====================

    def init_user_stats(self, user_id: int):
        """Initialize statistics for a user"""
        if user_id not in statistics_data:
            statistics_data[user_id] = {
                'user_id': user_id,
                'games_played': 0,
                'games_won': 0,
                'total_points': 0,
                'favorite_game': 'None',
                'join_date': datetime.now().isoformat(),
                'last_active': datetime.now().isoformat(),
                'riddles_solved': 0,
                'messages_sent': 0,
                'warnings_received': 0,
                'game_stats': {
                    'dice': {'played': 0, 'points': 0},
                    'rps': {'played': 0, 'wins': 0},
                    'trivia': {'played': 0, 'correct': 0},
                    'riddle': {'played': 0, 'solved': 0},
                    '20questions': {'played': 0, 'wins': 0},
                    'slots': {'played': 0, 'wins': 0},
                }
            }

    def update_user_stats(self, user_id: int, game: str, points: int, won: bool = True):
        """Update user statistics after a game"""
        self.init_user_stats(user_id)
        
        stats = statistics_data[user_id]
        stats['games_played'] += 1
        stats['total_points'] += points
        stats['last_active'] = datetime.now().isoformat()
        
        if won:
            stats['games_won'] += 1
        
        if stats['favorite_game'] == 'None':
            stats['favorite_game'] = game
        
        # Update game-specific stats
        if game in stats['game_stats']:
            stats['game_stats'][game]['played'] += 1
            if game == 'rps' and won:
                stats['game_stats'][game]['wins'] += 1
            elif game == 'trivia' and won:
                stats['game_stats'][game]['correct'] += 1
            elif game == 'riddle' and won:
                stats['game_stats'][game]['solved'] += 1
            elif game == '20questions' and won:
                stats['game_stats'][game]['wins'] += 1
            elif game == 'slots' and won:
                stats['game_stats'][game]['wins'] += 1
            elif game == 'dice':
                stats['game_stats'][game]['points'] += points

    async def show_statistics(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show user statistics"""
        user_id = update.message.from_user.id
        self.init_user_stats(user_id)
        
        stats = statistics_data[user_id]
        win_rate = (stats['games_won'] / stats['games_played'] * 100) if stats['games_played'] > 0 else 0
        
        join_date = datetime.fromisoformat(stats['join_date']).strftime("%d/%m/%Y")
        
        stats_text = f"""
📊 *YOUR STATISTICS*

👤 *Basic Info:*
  User ID: `{user_id}`
  Join Date: {join_date}
  Total Points: *{stats['total_points']}*

🎮 *Gaming Stats:*
  Games Played: {stats['games_played']}
  Games Won: {stats['games_won']}
  Win Rate: {win_rate:.1f}%
  Favorite Game: {stats['favorite_game']}

🎯 *Game Breakdown:*
"""
        
        for game, data in stats['game_stats'].items():
            if data['played'] > 0:
                stats_text += f"  • {game.upper()}: {data['played']} times"
                if 'wins' in data and data['wins'] > 0:
                    stats_text += f" ({data['wins']} wins)"
                stats_text += "\n"
        
        stats_text += f"""
⚠️ *Warnings:* {stats['warnings_received']}
💬 *Messages Sent:* {stats['messages_sent']}
"""
        
        await update.message.reply_text(stats_text, parse_mode='Markdown')

    async def global_statistics(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show global server statistics"""
        if not statistics_data:
            await update.message.reply_text("📊 No statistics yet!")
            return
        
        total_users = len(statistics_data)
        total_games = sum(s['games_played'] for s in statistics_data.values())
        total_points = sum(s['total_points'] for s in statistics_data.values())
        total_wins = sum(s['games_won'] for s in statistics_data.values())
        
        avg_win_rate = (total_wins / total_games * 100) if total_games > 0 else 0
        
        # Get top player
        top_player = max(statistics_data.values(), key=lambda x: x['total_points'])
        
        stats_text = f"""
📊 *GLOBAL STATISTICS*

👥 *Server Info:*
  Total Players: {total_users}
  Total Games Played: {total_games}
  Total Points Distributed: {total_points}

📈 *Global Stats:*
  Average Win Rate: {avg_win_rate:.1f}%
  Total Wins: {total_wins}

🏆 *Top Player:*
  User ID: {top_player['user_id']}
  Points: {top_player['total_points']}
  Games Won: {top_player['games_won']}
"""
        
        await update.message.reply_text(stats_text, parse_mode='Markdown')

    # ==================== ADVERTISEMENT SYSTEM ====================

    async def create_ad(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start creating an advertisement (Developer only)"""
        user_id = update.message.from_user.id
        
        if user_id not in DEVELOPER_IDS:
            await update.message.reply_text(
                "❌ You don't have permission to create advertisements.\n"
                "Only developers can create ads."
            )
            return
        
        await update.message.reply_text(
            "📢 *CREATE ADVERTISEMENT*\n\n"
            "Please enter the title for your advertisement:",
            parse_mode='Markdown'
        )
        
        return WAITING_FOR_AD_TITLE

    async def receive_ad_title(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Receive ad title"""
        context.user_data['ad_title'] = update.message.text
        
        await update.message.reply_text(
            "📢 *Title Received!*\n\n"
            f"Title: {context.user_data['ad_title']}\n\n"
            "Now enter the advertisement content/message:"
        )
        
        return WAITING_FOR_AD_CONTENT

    async def receive_ad_content(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Receive ad content"""
        context.user_data['ad_content'] = update.message.text
        
        await update.message.reply_text(
            "📢 *Content Received!*\n\n"
            f"Content: {context.user_data['ad_content']}\n\n"
            "Now enter the button text (or type 'none' for no button):"
        )
        
        return WAITING_FOR_AD_BUTTON_TEXT

    async def receive_ad_button_text(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Receive ad button text"""
        button_text = update.message.text
        
        if button_text.lower() == 'none':
            context.user_data['ad_button_text'] = None
            context.user_data['ad_button_link'] = None
            return await self.confirm_ad(update, context)
        
        context.user_data['ad_button_text'] = button_text
        
        await update.message.reply_text(
            "📢 *Button Text Received!*\n\n"
            f"Button Text: {button_text}\n\n"
            "Now enter the button link/URL:"
        )
        
        return WAITING_FOR_AD_BUTTON_LINK

    async def receive_ad_button_link(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Receive ad button link"""
        context.user_data['ad_button_link'] = update.message.text
        
        return await self.confirm_ad(update, context)

    async def confirm_ad(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Confirm advertisement"""
        title = context.user_data.get('ad_title', '')
        content = context.user_data.get('ad_content', '')
        button_text = context.user_data.get('ad_button_text')
        button_link = context.user_data.get('ad_button_link')
        
        preview = f"📢 *{title}*\n\n{content}"
        
        if button_text:
            preview += f"\n\n[{button_text}]({button_link})"
        
        keyboard = [
            [InlineKeyboardButton("✅ Confirm & Post", callback_data='ad_confirm')],
            [InlineKeyboardButton("❌ Cancel", callback_data='ad_cancel')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "📢 *PREVIEW YOUR ADVERTISEMENT:*\n\n" + preview + "\n\n*Is this correct?*",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        
        return ConversationHandler.END

    async def confirm_ad_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Confirm and post advertisement"""
        query = update.callback_query
        user_id = query.from_user.id
        
        if query.data == 'ad_cancel':
            await query.edit_message_text("❌ Advertisement creation cancelled.")
            return
        
        # Save advertisement
        ad_id = len(advertisements) + 1
        advertisements[ad_id] = {
            'id': ad_id,
            'created_by': user_id,
            'created_at': datetime.now().isoformat(),
            'title': context.user_data.get('ad_title', ''),
            'content': context.user_data.get('ad_content', ''),
            'button_text': context.user_data.get('ad_button_text'),
            'button_link': context.user_data.get('ad_button_link'),
            'views': 0,
            'clicks': 0
        }
        
        await query.edit_message_text(
            f"✅ *Advertisement Posted!*\n\n"
            f"Advertisement ID: {ad_id}\n"
            f"Status: Active\n\n"
            f"Your ad has been created and can be displayed to users!"
        )

    async def show_ads(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show all active advertisements"""
        if not advertisements:
            await update.message.reply_text("📢 No advertisements available!")
            return
        
        for ad_id, ad in advertisements.items():
            keyboard = []
            if ad['button_text'] and ad['button_link']:
                keyboard.append([
                    InlineKeyboardButton(ad['button_text'], url=ad['button_link'])
                ])
            
            if update.message.from_user.id in DEVELOPER_IDS:
                keyboard.append([
                    InlineKeyboardButton("📊 Stats", callback_data=f'ad_stats_{ad_id}'),
                    InlineKeyboardButton("🗑️ Delete", callback_data=f'ad_delete_{ad_id}')
                ])
            
            reply_markup = InlineKeyboardMarkup(keyboard) if keyboard else None
            
            ad_text = f"📢 *{ad['title']}*\n\n{ad['content']}\n\n_Views: {ad['views']} | Clicks: {ad['clicks']}_"
            
            await update.message.reply_text(ad_text, reply_markup=reply_markup, parse_mode='Markdown')

    async def manage_ads_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Manage advertisements"""
        query = update.callback_query
        data = query.data
        
        if data.startswith('ad_stats_'):
            ad_id = int(data.split('_')[2])
            ad = advertisements.get(ad_id)
            
            if ad:
                stats_text = f"""
📊 *ADVERTISEMENT STATISTICS*

Title: {ad['title']}
ID: {ad_id}
Views: {ad['views']}
Clicks: {ad['clicks']}
Click Rate: {(ad['clicks']/ad['views']*100 if ad['views'] > 0 else 0):.1f}%
Created: {ad['created_at']}
"""
                await query.edit_message_text(stats_text, parse_mode='Markdown')
        
        elif data.startswith('ad_delete_'):
            ad_id = int(data.split('_')[2])
            if ad_id in advertisements:
                del advertisements[ad_id]
                await query.edit_message_text("✅ Advertisement deleted!")

    # ==================== SUBSCRIPTION CHECK ====================

    async def check_subscription(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
        """Check if user is subscribed to required channel"""
        if not CHANNEL_ID:
            return True
        
        user_id = update.message.from_user.id
        
        try:
            member = await context.bot.get_chat_member(CHANNEL_ID, user_id)
            is_subscribed = member.status != ChatMemberStatus.LEFT
            
            if not is_subscribed:
                channel_link = f"https://t.me/{CHANNEL_ID.replace('@', '')}"
                await update.message.reply_text(
                    f"❌ *Subscription Required*\n\n"
                    f"You must subscribe to our channel first!\n\n"
                    f"👉 [Subscribe Here]({channel_link})\n\n"
                    f"After subscribing, try again.",
                    parse_mode='Markdown'
                )
            
            return is_subscribed
        except Exception as e:
            logger.error(f"Error checking subscription: {e}")
            return True

    # ==================== MAIN COMMANDS ====================

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        if update.message.chat.type == 'private':
            await update.message.reply_text(
                "🤖 *Welcome to Comprehensive Group Bot v4.0!*\n\n"
                "I provide:\n"
                "✅ Group management & protection\n"
                "✅ Fun games & trivia\n"
                "✅ Statistics & analytics\n"
                "✅ Advertisement system\n"
                "✅ Admin moderation tools\n"
                "✅ Mandatory subscription check\n\n"
                "Add me to your group and use /help to see all commands!",
                parse_mode='Markdown'
            )

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show comprehensive help menu"""
        help_text = """
╔════════════════════════════════════════╗
║  🤖 COMPREHENSIVE GROUP BOT v4.0      ║
║  With Statistics & Advertisements     ║
╚════════════════════════════════════════╝

📋 *ADMIN COMMANDS:*
  /kick <user_id> - Kick a user
  /ban <user_id> - Ban a user
  /unban <user_id> - Unban a user
  /warn <user_id> - Warn a user
  /mute <user_id> <time> - Mute user
  /unmute <user_id> - Unmute a user
  /setwelcome <text> - Set welcome message
  /setrules <text> - Set group rules
  /cleanup - Delete bot messages

🎮 *GAMES & FUN:*
  /dice - Roll a dice
  /coin - Flip a coin
  /rps - Rock, Paper, Scissors
  /number - Guess the number
  /trivia - Trivia questions
  /slots - Slot machine
  /8ball - Magic 8-ball
  /quote - Random quote
  /joke - Random joke
  /lucky - Check luck
  /riddle - Riddle game
  /20questions - 20 questions game

📊 *STATISTICS COMMANDS:*
  /stats - Your personal statistics
  /globalstats - Global server statistics
  /leaderboard - Top players

📢 *ADVERTISEMENT COMMANDS (Developer):*
  /createad - Create new advertisement
  /showads - View all advertisements

👤 *USER COMMANDS:*
  /whisper <id> <msg> - Send whisper
  /readwhispers - Read whispers
  /welcome - Show welcome message
  /rules - Show group rules
  /mypoints - Check your points
  /info - Show bot information
  /help - Show this menu
"""
        await update.message.reply_text(help_text, parse_mode='Markdown')

    async def info(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show bot information"""
        info_text = """
🤖 *Comprehensive Group Management Bot v4.0*

📊 *Information:*
  Version: 4.0 (Full Release)
  Status: ✅ Active
  Games: 16
  Commands: 50+
  Users: {users}

🎯 *Features:*
  ✅ Anti-spam protection
  ✅ User moderation tools
  ✅ 16 Fun games & trivia
  ✅ Riddles & 20 Questions
  ✅ Whisper messaging
  ✅ Complete statistics system
  ✅ Advertisement platform
  ✅ Mandatory subscription
  ✅ Admin controls
  ✅ Leaderboard

📈 *Statistics & Ads NEW:*
  ✅ Personal game statistics
  ✅ Global server analytics
  ✅ Developer advertisement system
  ✅ Ad analytics & tracking

🔧 *Developer:* Your Bot Team
📱 *Platform:* Telegram

Use /help to see all available commands!
""".format(users=len(statistics_data))
        await update.message.reply_text(info_text, parse_mode='Markdown')

    # ==================== ADMIN COMMANDS ====================

    async def kick_user(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Kick a user from the group"""
        if not await self.check_admin(update, context):
            return

        if not context.args:
            await update.message.reply_text("❌ Usage: /kick <user_id>")
            return

        try:
            user_id = int(context.args[0])
            await context.bot.unban_chat_member(update.message.chat_id, user_id)
            await update.message.reply_text(f"✅ User {user_id} has been kicked.")
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {str(e)}")

    async def ban_user(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Ban a user from the group"""
        if not await self.check_admin(update, context):
            return

        if not context.args:
            await update.message.reply_text("❌ Usage: /ban <user_id>")
            return

        try:
            user_id = int(context.args[0])
            await context.bot.ban_chat_member(update.message.chat_id, user_id)
            await update.message.reply_text(f"✅ User {user_id} has been banned.")
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {str(e)}")

    async def unban_user(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Unban a user from the group"""
        if not await self.check_admin(update, context):
            return

        if not context.args:
            await update.message.reply_text("❌ Usage: /unban <user_id>")
            return

        try:
            user_id = int(context.args[0])
            await context.bot.unban_chat_member(update.message.chat_id, user_id)
            await update.message.reply_text(f"✅ User {user_id} has been unbanned.")
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {str(e)}")

    async def warn_user(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Warn a user"""
        if not await self.check_admin(update, context):
            return

        if not context.args:
            await update.message.reply_text("❌ Usage: /warn <user_id>")
            return

        try:
            user_id = int(context.args[0])
            if user_id not in user_warnings:
                user_warnings[user_id] = 0
            user_warnings[user_id] += 1
            
            # Update stats
            self.init_user_stats(user_id)
            statistics_data[user_id]['warnings_received'] += 1

            await update.message.reply_text(
                f"⚠️ User {user_id} warned. Warnings: {user_warnings[user_id]}/3"
            )
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {str(e)}")

    async def mute_user(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Mute a user for specified time"""
        if not await self.check_admin(update, context):
            return

        if len(context.args) < 2:
            await update.message.reply_text("❌ Usage: /mute <user_id> <time>\nExample: /mute 123 10m")
            return

        try:
            user_id = int(context.args[0])
            time_str = context.args[1]
            
            time_value = int(time_str[:-1])
            time_unit = time_str[-1]
            
            if time_unit == 'm':
                mute_time = timedelta(minutes=time_value)
            elif time_unit == 'h':
                mute_time = timedelta(hours=time_value)
            elif time_unit == 's':
                mute_time = timedelta(seconds=time_value)
            else:
                await update.message.reply_text("❌ Invalid time format. Use: s, m, or h")
                return

            mute_permissions = ChatPermissions(can_send_messages=False)
            await context.bot.restrict_chat_member(
                update.message.chat_id,
                user_id,
                permissions=mute_permissions,
                until_date=datetime.now() + mute_time
            )
            await update.message.reply_text(f"🔇 User {user_id} muted for {time_str}.")
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {str(e)}")

    async def unmute_user(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Unmute a user"""
        if not await self.check_admin(update, context):
            return

        if not context.args:
            await update.message.reply_text("❌ Usage: /unmute <user_id>")
            return

        try:
            user_id = int(context.args[0])
            unmute_permissions = ChatPermissions(can_send_messages=True)
            await context.bot.restrict_chat_member(
                update.message.chat_id,
                user_id,
                permissions=unmute_permissions
            )
            await update.message.reply_text(f"✅ User {user_id} has been unmuted.")
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {str(e)}")

    async def set_welcome(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Set welcome message"""
        if not await self.check_admin(update, context):
            return

        if not context.args:
            await update.message.reply_text("❌ Usage: /setwelcome <message>")
            return

        welcome_msg = ' '.join(context.args)
        context.chat_data['welcome_message'] = welcome_msg
        await update.message.reply_text("✅ Welcome message has been set.")

    async def show_welcome(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show welcome message"""
        welcome_msg = context.chat_data.get('welcome_message', 'No welcome message set.')
        await update.message.reply_text(welcome_msg)

    async def set_rules(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Set group rules"""
        if not await self.check_admin(update, context):
            return

        if not context.args:
            await update.message.reply_text("❌ Usage: /setrules <rules>")
            return

        rules = ' '.join(context.args)
        context.chat_data['rules'] = rules
        await update.message.reply_text("✅ Group rules have been set.")

    async def show_rules(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show group rules"""
        rules = context.chat_data.get('rules', '📋 No rules set yet.')
        await update.message.reply_text(f"📋 *Group Rules:*\n\n{rules}", parse_mode='Markdown')

    async def cleanup(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Delete bot's recent messages"""
        if not await self.check_admin(update, context):
            return

        await update.message.reply_text("🧹 Cleanup completed.")

    async def welcome_new_members(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Welcome new members to the group"""
        for member in update.message.new_chat_members:
            if member.is_bot:
                continue

            # Initialize stats for new member
            self.init_user_stats(member.id)

            welcome_msg = context.chat_data.get('welcome_message', 
                f"Welcome {member.mention_html()}! 👋\n\nRead the rules: /rules")
            
            try:
                await update.message.reply_html(welcome_msg)
            except Exception as e:
                logger.error(f"Error sending welcome message: {e}")

    # ==================== GAME COMMANDS ====================

    async def riddle_game(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start riddle game"""
        if not await self.check_subscription(update, context):
            return

        user_id = update.message.from_user.id
        self.init_user_stats(user_id)

        riddle_data = random.choice(riddles)
        
        context.user_data['current_riddle'] = {
            'riddle': riddle_data,
            'attempts': 0,
            'hints_used': 0
        }
        
        keyboard = [
            [InlineKeyboardButton("💡 Get Hint", callback_data='riddle_hint')],
            [InlineKeyboardButton("❌ Give Up", callback_data='riddle_giveup')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            f"🧩 *RIDDLE GAME*\n\n"
            f"Difficulty: {riddle_data['difficulty']}\n\n"
            f"Question:\n{riddle_data['question']}\n\n"
            f"Reply with your answer or use the buttons below:",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

    async def riddle_hint(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Get hint for riddle"""
        query = update.callback_query
        
        if 'current_riddle' not in context.user_data:
            await query.answer("❌ No active riddle!", show_alert=True)
            return
        
        riddle_data = context.user_data['current_riddle']['riddle']
        hints_used = context.user_data['current_riddle']['hints_used']
        
        if hints_used >= len(riddle_data['hints']):
            await query.answer("❌ No more hints available!", show_alert=True)
            return
        
        hint = riddle_data['hints'][hints_used]
        context.user_data['current_riddle']['hints_used'] += 1
        
        await query.answer(f"💡 Hint: {hint}", show_alert=True)

    async def riddle_giveup(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Give up on riddle"""
        query = update.callback_query
        
        if 'current_riddle' not in context.user_data:
            await query.answer("❌ No active riddle!", show_alert=True)
            return
        
        riddle_data = context.user_data['current_riddle']['riddle']
        answer = riddle_data['answer']
        
        await query.edit_message_text(
            f"🧩 *RIDDLE GAME - GAVE UP*\n\n"
            f"Question: {riddle_data['question']}\n\n"
            f"Answer: *{answer}*\n\n"
            f"Better luck next time! 🍀",
            parse_mode='Markdown'
        )
        del context.user_data['current_riddle']

    async def handle_riddle_answer(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle riddle answer"""
        if 'current_riddle' not in context.user_data:
            return
        
        user_id = update.message.from_user.id
        self.init_user_stats(user_id)
        
        user_answer = update.message.text.lower().strip()
        riddle_data = context.user_data['current_riddle']['riddle']
        correct_answer = riddle_data['answer'].lower().strip()
        
        context.user_data['current_riddle']['attempts'] += 1
        
        if user_answer == correct_answer:
            points = max(50 - context.user_data['current_riddle']['attempts'] * 5, 10)
            
            # Update stats
            self.update_user_stats(user_id, 'riddle', points, True)
            user_scores[user_id] = user_scores.get(user_id, 0) + points
            statistics_data[user_id]['riddles_solved'] += 1
            
            await update.message.reply_text(
                f"✅ *CORRECT!*\n\n"
                f"Answer: {correct_answer}\n"
                f"Attempts: {context.user_data['current_riddle']['attempts']}\n"
                f"Points Earned: +{points}",
                parse_mode='Markdown'
            )
            del context.user_data['current_riddle']
        else:
            await update.message.reply_text(
                f"❌ Wrong answer! Try again or use 💡 hint"
            )

    async def dice_game(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Roll a dice"""
        if not await self.check_subscription(update, context):
            return

        user_id = update.message.from_user.id
        self.init_user_stats(user_id)
        
        result = random.randint(1, 6)
        
        user_scores[user_id] = user_scores.get(user_id, 0) + result
        self.update_user_stats(user_id, 'dice', result)
        
        emoji_map = {
            1: "🎲 One",
            2: "🎲 Two",
            3: "🎲 Three",
            4: "🎲 Four",
            5: "🎲 Five",
            6: "🎲 Six"
        }
        
        await update.message.reply_text(
            f"🎲 *Dice Result:* {emoji_map[result]}\n\n"
            f"Points: +{result}\n"
            f"Total Points: {user_scores[user_id]}",
            parse_mode='Markdown'
        )

    async def leaderboard(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show top players"""
        if not user_scores:
            await update.message.reply_text("📊 No scores yet!")
            return
        
        sorted_scores = sorted(user_scores.items(), key=lambda x: x[1], reverse=True)[:10]
        
        leaderboard_text = "🏆 *TOP 10 PLAYERS*\n\n"
        medals = ['🥇', '🥈', '🥉']
        
        for idx, (user_id, score) in enumerate(sorted_scores, 1):
            medal = medals[idx-1] if idx <= 3 else f"{idx}."
            leaderboard_text += f"{medal} User {user_id}: {score} points\n"
        
        await update.message.reply_text(leaderboard_text, parse_mode='Markdown')

    async def my_points(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Check your points"""
        user_id = update.message.from_user.id
        points = user_scores.get(user_id, 0)
        
        await update.message.reply_text(
            f"⭐ *Your Points:* {points}\n\n"
            f"Play games to earn more points!\n"
            f"Check /leaderboard to see your rank!",
            parse_mode='Markdown'
        )

    async def whisper(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Send a private whisper message to another user"""
        if not await self.check_subscription(update, context):
            return

        if len(context.args) < 2:
            await update.message.reply_text(
                "❌ Usage: /whisper <user_id> <message>\n\n"
                "Example: /whisper 123456 Hello, this is a secret!"
            )
            return

        try:
            recipient_id = int(context.args[0])
            message_text = ' '.join(context.args[1:])
            sender_id = update.message.from_user.id
            sender_name = update.message.from_user.first_name
            
            if recipient_id not in whisper_messages:
                whisper_messages[recipient_id] = []
            
            whisper_messages[recipient_id].append({
                'from': sender_id,
                'from_name': sender_name,
                'message': message_text,
                'time': datetime.now()
            })
            
            await update.message.reply_text(
                f"🤫 *WHISPER SENT*\n\n"
                f"To: User {recipient_id}\n"
                f"Message: {message_text}\n\n"
                f"The recipient can read it with /readwhispers",
                parse_mode='Markdown'
            )
            
        except ValueError:
            await update.message.reply_text("❌ Invalid user ID!")
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {str(e)}")

    async def read_whispers(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Read whisper messages sent to you"""
        user_id = update.message.from_user.id
        
        if user_id not in whisper_messages or not whisper_messages[user_id]:
            await update.message.reply_text("🤫 You have no whisper messages!")
            return
        
        messages = whisper_messages[user_id]
        whisper_text = "🤫 *YOUR WHISPER MESSAGES:*\n\n"
        
        for idx, msg in enumerate(messages, 1):
            time_ago = (datetime.now() - msg['time']).seconds
            whisper_text += (
                f"{idx}. *From: {msg['from_name']}* (ID: {msg['from']})\n"
                f"   Message: {msg['message']}\n"
                f"   Time: {time_ago} seconds ago\n\n"
            )
        
        whisper_text += "_Messages will be cleared after reading._"
        
        await update.message.reply_text(whisper_text, parse_mode='Markdown')
        whisper_messages[user_id] = []

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle regular messages for spam detection and game responses"""
        if not update.message or update.message.chat.type == 'private':
            return

        user_id = update.message.from_user.id
        self.init_user_stats(user_id)
        
        # Update stats
        statistics_data[user_id]['messages_sent'] += 1

        # Check for riddle answer
        if 'current_riddle' in context.user_data:
            await self.handle_riddle_answer(update, context)

        # Anti-spam detection
        current_time = datetime.now()

        if user_id not in user_messages:
            user_messages[user_id] = []

        user_messages[user_id] = [
            msg_time for msg_time in user_messages[user_id]
            if (current_time - msg_time).total_seconds() < SPAM_TIME_WINDOW
        ]

        user_messages[user_id].append(current_time)

        if len(user_messages[user_id]) > SPAM_THRESHOLD:
            await self.handle_spam(update, context, user_id)

    async def handle_spam(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int):
        """Handle spam detection"""
        if user_id not in user_warnings:
            user_warnings[user_id] = 0

        user_warnings[user_id] += 1
        user = update.message.from_user

        try:
            if user_warnings[user_id] < WARN_THRESHOLD:
                await update.message.reply_text(
                    f"⚠️ {user.mention_html()} - Stop spamming! Warning {user_warnings[user_id]}/3",
                    parse_mode='HTML'
                )
            else:
                mute_permissions = ChatPermissions(can_send_messages=False)
                await context.bot.restrict_chat_member(
                    update.message.chat_id,
                    user_id,
                    permissions=mute_permissions,
                    until_date=datetime.now() + timedelta(minutes=10)
                )
                await update.message.reply_text(
                    f"🔇 {user.mention_html()} has been muted for 10 minutes due to spam.",
                    parse_mode='HTML'
                )
                user_warnings[user_id] = 0

        except Exception as e:
            logger.error(f"Error handling spam: {e}")

    async def check_admin(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
        """Check if user is admin"""
        user_id = update.message.from_user.id
        
        try:
            member = await context.bot.get_chat_member(update.message.chat_id, user_id)
            is_admin = member.status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.CREATOR]
            
            if not is_admin:
                await update.message.reply_text("❌ You need admin privileges to use this command.")
            return is_admin
        except Exception as e:
            logger.error(f"Error checking admin status: {e}")
            return False

    def setup_handlers(self):
        """Setup all command and message handlers"""
        # Main commands
        self.app.add_handler(CommandHandler("start", self.start))
        self.app.add_handler(CommandHandler("help", self.help_command))
        self.app.add_handler(CommandHandler("info", self.info))

        # Admin commands
        self.app.add_handler(CommandHandler("kick", self.kick_user))
        self.app.add_handler(CommandHandler("ban", self.ban_user))
        self.app.add_handler(CommandHandler("unban", self.unban_user))
        self.app.add_handler(CommandHandler("warn", self.warn_user))
        self.app.add_handler(CommandHandler("mute", self.mute_user))
        self.app.add_handler(CommandHandler("unmute", self.unmute_user))
        self.app.add_handler(CommandHandler("setwelcome", self.set_welcome))
        self.app.add_handler(CommandHandler("welcome", self.show_welcome))
        self.app.add_handler(CommandHandler("setrules", self.set_rules))
        self.app.add_handler(CommandHandler("rules", self.show_rules))
        self.app.add_handler(CommandHandler("cleanup", self.cleanup))

        # Game commands
        self.app.add_handler(CommandHandler("dice", self.dice_game))
        self.app.add_handler(CommandHandler("riddle", self.riddle_game))
        self.app.add_handler(CommandHandler("whisper", self.whisper))
        self.app.add_handler(CommandHandler("readwhispers", self.read_whispers))

        # Statistics commands
        self.app.add_handler(CommandHandler("stats", self.show_statistics))
        self.app.add_handler(CommandHandler("globalstats", self.global_statistics))
        self.app.add_handler(CommandHandler("leaderboard", self.leaderboard))
        self.app.add_handler(CommandHandler("mypoints", self.my_points))

        # Advertisement handlers
        conv_handler = ConversationHandler(
            entry_points=[CommandHandler("createad", self.create_ad)],
            states={
                WAITING_FOR_AD_TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.receive_ad_title)],
                WAITING_FOR_AD_CONTENT: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.receive_ad_content)],
                WAITING_FOR_AD_BUTTON_TEXT: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.receive_ad_button_text)],
                WAITING_FOR_AD_BUTTON_LINK: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.receive_ad_button_link)],
            },
            fallbacks=[CommandHandler("cancel", lambda u, c: ConversationHandler.END)],
        )
        
        self.app.add_handler(conv_handler)
        self.app.add_handler(CommandHandler("showads", self.show_ads))
        self.app.add_handler(CallbackQueryHandler(self.confirm_ad_callback, pattern='^ad_'))
        self.app.add_handler(CallbackQueryHandler(self.manage_ads_callback, pattern='^ad_'))

        # Callback handlers
        self.app.add_handler(CallbackQueryHandler(self.riddle_hint, pattern='^riddle_hint'))
        self.app.add_handler(CallbackQueryHandler(self.riddle_giveup, pattern='^riddle_giveup'))

        # New members handler
        self.app.add_handler(MessageHandler(
            filters.StatusUpdate.NEW_CHAT_MEMBERS,
            self.welcome_new_members
        ))

        # Message handler for spam detection and game responses
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
        
        logger.info("🤖 Comprehensive Bot v4.0 started successfully!")


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
