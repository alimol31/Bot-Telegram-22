#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
بوت تيليجرام متكامل ومطور مع الألعاب ونظام المال ونظام الإدمن المتقدم
الإصدار: 2.0
"""

import logging
import json
import random
import asyncio
import os
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
from telegram.error import TelegramError, Forbidden, BadRequest

# إعدادات التسجيل المتقدمة
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler('bot.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ===== إعدادات البوت =====
BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"
ADMIN_IDS = [123456789]  # قائمة معرفات المشرفين
BOT_VERSION = "2.0"

# ملفات البيانات
DATA_FILE = "users_data.json"
MESSAGES_FILE = "messages_log.json"
SETTINGS_FILE = "bot_settings.json"

# الإعدادات الافتراضية
DEFAULT_SETTINGS = {
    "maintenance_mode": False,
    "maintenance_message": "البوت تحت الصيانة حاليا...",
    "min_bet": 5,
    "max_bet": 10000,
    "daily_reward_min": 50,
    "daily_reward_max": 200,
    "starting_balance": 1000,
    "level_up_bonus": 100,
    "transfer_fee": 0.02,  # 2% رسوم التحويل
    "welcome_bonus": 500
}

class EnhancedGameBot:
    def __init__(self):
        self.users_data = self.load_data()
        self.messages_log = self.load_messages()
        self.settings = self.load_settings()
        self.create_backup_folder()
        
    def create_backup_folder(self):
        """إنشاء مجلد النسخ الاحتياطية"""
        if not os.path.exists("backups"):
            os.makedirs("backups")
    
    def load_data(self) -> Dict:
        """تحميل بيانات المستخدمين مع معالجة الأخطاء"""
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.warning(f"خطأ في تحميل بيانات المستخدمين: {e}")
            return {}
    
    def load_messages(self) -> Dict:
        """تحميل سجل الرسائل"""
        try:
            with open(MESSAGES_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}
    
    def load_settings(self) -> Dict:
        """تحميل إعدادات البوت"""
        try:
            with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
                settings = json.load(f)
                # دمج الإعدادات الافتراضية مع المحفوظة
                for key, value in DEFAULT_SETTINGS.items():
                    if key not in settings:
                        settings[key] = value
                return settings
        except (FileNotFoundError, json.JSONDecodeError):
            return DEFAULT_SETTINGS.copy()
    
    def save_data(self):
        """حفظ بيانات المستخدمين مع نسخة احتياطية"""
        try:
            # إنشاء نسخة احتياطية
            if os.path.exists(DATA_FILE):
                backup_name = f"backups/users_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                with open(DATA_FILE, 'r', encoding='utf-8') as old_file:
                    with open(backup_name, 'w', encoding='utf-8') as backup_file:
                        backup_file.write(old_file.read())
            
            # حفظ البيانات الجديدة
            with open(DATA_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.users_data, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            logger.error(f"خطأ في حفظ البيانات: {e}")
    
    def save_messages(self):
        """حفظ سجل الرسائل"""
        try:
            with open(MESSAGES_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.messages_log, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"خطأ في حفظ الرسائل: {e}")
    
    def save_settings(self):
        """حفظ إعدادات البوت"""
        try:
            with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"خطأ في حفظ الإعدادات: {e}")
    
    def log_message(self, user_id: int, username: Optional[str], first_name: Optional[str], 
                   last_name: Optional[str], message_text: str):
        """تسجيل الرسائل مع معالجة محسنة"""
        try:
            user_id = str(user_id)
            if user_id not in self.messages_log:
                self.messages_log[user_id] = {
                    'username': username or 'غير محدد',
                    'first_name': first_name or 'غير محدد',
                    'last_name': last_name or '',
                    'messages': [],
                    'message_count': 0,
                    'first_seen': datetime.now().isoformat(),
                    'last_seen': datetime.now().isoformat()
                }
            
            # تحديث معلومات المستخدم
            self.messages_log[user_id].update({
                'username': username or 'غير محدد',
                'first_name': first_name or 'غير محدد',
                'last_name': last_name or '',
                'last_seen': datetime.now().isoformat()
            })
            
            # إضافة الرسالة مع تحديد طولها
            message_entry = {
                'text': message_text[:500],  # الحد من طول الرسالة المحفوظة
                'timestamp': datetime.now().isoformat(),
                'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'length': len(message_text)
            }
            
            self.messages_log[user_id]['messages'].append(message_entry)
            self.messages_log[user_id]['message_count'] += 1
            
            # الاحتفاظ بآخر 100 رسالة لكل مستخدم
            if len(self.messages_log[user_id]['messages']) > 100:
                self.messages_log[user_id]['messages'] = self.messages_log[user_id]['messages'][-100:]
            
            # حفظ تلقائي كل 50 رسالة
            if self.messages_log[user_id]['message_count'] % 50 == 0:
                self.save_messages()
                
        except Exception as e:
            logger.error(f"خطأ في تسجيل الرسالة: {e}")
    
    def get_user_data(self, user_id: int) -> Dict[str, Any]:
        """الحصول على بيانات المستخدم مع الإعدادات المحدثة"""
        user_id = str(user_id)
        if user_id not in self.users_data:
            self.users_data[user_id] = {
                'balance': self.settings['starting_balance'],
                'wins': 0,
                'losses': 0,
                'games_played': 0,
                'last_daily': None,
                'level': 1,
                'exp': 0,
                'achievements': [],
                'is_banned': False,
                'ban_reason': None,
                'ban_date': None,
                'join_date': datetime.now().isoformat(),
                'total_wagered': 0,
                'total_won': 0,
                'total_lost': 0,
                'favorite_game': None,
                'vip_status': False,
                'referral_count': 0,
                'referred_by': None,
                'daily_streak': 0,
                'last_activity': datetime.now().isoformat()
            }
            self.save_data()
        
        # تحديث آخر نشاط
        self.users_data[user_id]['last_activity'] = datetime.now().isoformat()
        return self.users_data[user_id]
    
    def update_user_data(self, user_id: int, data: Dict[str, Any]):
        """تحديث بيانات المستخدم"""
        try:
            self.users_data[str(user_id)].update(data)
            self.save_data()
        except Exception as e:
            logger.error(f"خطأ في تحديث بيانات المستخدم {user_id}: {e}")
    
    def calculate_level_up_exp(self, level: int) -> int:
        """حساب النقاط المطلوبة للمستوى التالي"""
        return level * 150 + (level * level * 10)
    
    def check_achievements(self, user_id: int, user_data: Dict) -> str:
        """فحص الإنجازات الجديدة"""
        achievements = []
        current_achievements = set(user_data.get('achievements', []))
        
        # إنجازات الألعاب
        if user_data['games_played'] >= 100 and 'games_100' not in current_achievements:
            achievements.append('games_100')
            user_data['achievements'].append('games_100')
            
        if user_data['wins'] >= 50 and 'wins_50' not in current_achievements:
            achievements.append('wins_50')
            user_data['achievements'].append('wins_50')
            
        # إنجازات المال
        if user_data['balance'] >= 10000 and 'rich_10k' not in current_achievements:
            achievements.append('rich_10k')
            user_data['achievements'].append('rich_10k')
            
        # إنجازات المستوى
        if user_data['level'] >= 10 and 'level_10' not in current_achievements:
            achievements.append('level_10')
            user_data['achievements'].append('level_10')
        
        if achievements:
            self.update_user_data(user_id, user_data)
            achievement_names = {
                'games_100': '🎮 لاعب محترف - 100 لعبة',
                'wins_50': '🏆 المنتصر - 50 انتصار',
                'rich_10k': '💰 الثري - 10,000 كوين',
                'level_10': '⭐ الخبير - المستوى 10'
            }
            return "🏅 إنجاز جديد!\n" + "\n".join([achievement_names.get(a, a) for a in achievements])
        
        return ""
    
    def is_maintenance_mode(self) -> bool:
        """التحقق من وضع الصيانة"""
        return self.settings.get('maintenance_mode', False)

# إنشاء كائن البوت المحسن
game_bot = EnhancedGameBot()

# ===== وظائف مساعدة =====

def is_admin(user_id: int) -> bool:
    """التحقق من صلاحية الإدمن"""
    return user_id in ADMIN_IDS

def admin_only(func):
    """ديكوريتر للأوامر المقتصرة على الإدمن"""
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not is_admin(update.effective_user.id):
            await update.message.reply_text("❌ هذا الأمر مخصص للمشرفين فقط!")
            return
        return await func(update, context)
    return wrapper

def maintenance_check(func):
    """ديكوريتر للتحقق من وضع الصيانة"""
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if game_bot.is_maintenance_mode() and not is_admin(update.effective_user.id):
            await update.message.reply_text(
                f"🔧 {game_bot.settings['maintenance_message']}\n"
                f"عذراً للإزعاج، سنعود قريباً!"
            )
            return
        return await func(update, context)
    return wrapper

def ban_check(func):
    """ديكوريتر للتحقق من حظر المستخدم"""
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_data = game_bot.get_user_data(update.effective_user.id)
        if user_data.get('is_banned', False) and not is_admin(update.effective_user.id):
            ban_reason = user_data.get('ban_reason', 'غير محدد')
            ban_date = user_data.get('ban_date', 'غير محدد')
            await update.message.reply_text(
                f"🚫 تم حظرك من استخدام البوت!\n"
                f"📅 تاريخ الحظر: {ban_date}\n"
                f"📝 السبب: {ban_reason}\n\n"
                f"للمراجعة تواصل مع المشرفين"
            )
            return
        return await func(update, context)
    return wrapper

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """معالج الأخطاء العام"""
    logger.error(f"استثناء أثناء معالجة التحديث: {context.error}")
    
    if isinstance(update, Update) and update.effective_message:
        try:
            await update.effective_message.reply_text(
                "❌ حدث خطأ غير متوقع. تم تسجيل المشكلة وسيتم إصلاحها قريباً."
            )
        except Exception as e:
            logger.error(f"فشل في إرسال رسالة الخطأ: {e}")

async def log_all_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """تسجيل جميع الرسائل"""
    if update.message and update.message.text and not update.message.text.startswith('/'):
        user = update.effective_user
        game_bot.log_message(
            user.id,
            user.username,
            user.first_name,
            user.last_name,
            update.message.text
        )

# ===== الأوامر الأساسية =====

@maintenance_check
@ban_check
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """أمر البداية المحسن"""
    user = update.effective_user
    user_data = game_bot.get_user_data(user.id)
    
    # تحقق من الدعوة
    referral_bonus = ""
    if context.args and len(context.args) > 0:
        try:
            referrer_id = int(context.args[0])
            if referrer_id != user.id and not user_data.get('referred_by'):
                referrer_data = game_bot.get_user_data(referrer_id)
                referrer_data['referral_count'] += 1
                referrer_data['balance'] += 100  # مكافأة الداعي
                user_data['referred_by'] = referrer_id
                user_data['balance'] += game_bot.settings['welcome_bonus']
                game_bot.update_user_data(referrer_id, referrer_data)
                game_bot.update_user_data(user.id, user_data)
                referral_bonus = f"\n🎉 تم قبول دعوتك! حصلت على {game_bot.settings['welcome_bonus']} كوين إضافية!"
        except (ValueError, IndexError):
            pass
    
    welcome_text = f"""
🎮 مرحباً {user.first_name}!

🌟 أهلاً بك في بوت الكازينو المتطور! 💰

💳 رصيدك الحالي: {user_data['balance']:,} كوين
🎯 المستوى: {user_data['level']} ({user_data['exp']}/{game_bot.calculate_level_up_exp(user_data['level'])} نقطة)
🏆 الانتصارات: {user_data['wins']} | 💀 الخسائر: {user_data['losses']}
📈 معدل الفوز: {(user_data['wins']/(user_data['games_played'] or 1)*100):.1f}%

🎲 الألعاب المتاحة:
• /roulette - الروليت الأوروبي
• /slots - آلة القمار المتطورة  
• /dice - لعبة النرد
• /coinflip - قلب العملة
• /blackjack - البلاك جاك
• /lottery - اليانصيب اليومي

💰 الخدمات المالية:
• /balance - عرض الرصيد التفصيلي
• /daily - المكافأة اليومية
• /transfer - تحويل الأموال
• /invest - الاستثمار

📊 المعلومات:
• /stats - إحصائياتك الشخصية
• /leaderboard - لوحة المتصدرين
• /achievements - إنجازاتك
• /referral - نظام الإحالة

{referral_bonus}

اختر لعبة واستمتع! 🎉
الإصدار: {BOT_VERSION}
"""
    
    # إضافة أوامر المشرف
    if is_admin(user.id):
        welcome_text += f"\n👑 أوامر المشرف:\n/admin - لوحة التحكم"
    
    keyboard = [
        [InlineKeyboardButton("🎲 الروليت", callback_data="game_roulette"),
         InlineKeyboardButton("🎰 القمار", callback_data="game_slots")],
        [InlineKeyboardButton("🎯 النرد", callback_data="game_dice"),
         InlineKeyboardButton("🪙 العملة", callback_data="game_coinflip")],
        [InlineKeyboardButton("🃏 البلاك جاك", callback_data="game_blackjack"),
         InlineKeyboardButton("🎫 اليانصيب", callback_data="game_lottery")],
        [InlineKeyboardButton("💰 الرصيد", callback_data="show_balance"),
         InlineKeyboardButton("🎁 المكافأة اليومية", callback_data="daily_reward")],
        [InlineKeyboardButton("📊 الإحصائيات", callback_data="show_stats"),
         InlineKeyboardButton("🏆 المتصدرون", callback_data="leaderboard")],
        [InlineKeyboardButton("🎖️ الإنجازات", callback_data="achievements"),
         InlineKeyboardButton("👥 الإحالة", callback_data="referral_info")]
    ]
    
    if is_admin(user.id):
        keyboard.append([InlineKeyboardButton("👑 لوحة التحكم", callback_data="admin_panel")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode='HTML')

@maintenance_check
@ban_check
async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """عرض الرصيد التفصيلي"""
    user_data = game_bot.get_user_data(update.effective_user.id)
    user = update.effective_user
    
    # حساب الإحصائيات
    win_rate = (user_data['wins'] / (user_data['games_played'] or 1)) * 100
    net_profit = user_data['total_won'] - user_data['total_lost']
    next_level_exp = game_bot.calculate_level_up_exp(user_data['level'])
    
    balance_text = f"""
💰 <b>تفاصيل حسابك</b> - {user.first_name}

💳 <b>الرصيد الحالي:</b> {user_data['balance']:,} كوين
🎯 <b>المستوى:</b> {user_data['level']} 
⭐ <b>النقاط:</b> {user_data['exp']:,} / {next_level_exp:,}
📊 <b>التقدم:</b> {(user_data['exp']/next_level_exp*100):.1f}%

🎮 <b>إحصائيات الألعاب:</b>
🏆 الانتصارات: {user_data['wins']:,}
💀 الخسائر: {user_data['losses']:,}
🎯 إجمالي الألعاب: {user_data['games_played']:,}
📈 معدل الفوز: {win_rate:.2f}%

💰 <b>الإحصائيات المالية:</b>
💵 إجمالي الرهان: {user_data['total_wagered']:,} كوين
💲 إجمالي الأرباح: {user_data['total_won']:,} كوين
💸 إجمالي الخسائر: {user_data['total_lost']:,} كوين
📊 صافي الربح: {net_profit:+,} كوين

🎖️ <b>الإنجازات:</b> {len(user_data['achievements'])}
👥 <b>الإحالات:</b> {user_data['referral_count']}
🔥 <b>سلسلة المكافأة:</b> {user_data['daily_streak']} يوم

{'🌟 <b>عضو VIP</b>' if user_data.get('vip_status') else ''}
"""
    
    keyboard = [
        [InlineKeyboardButton("🎁 المكافأة اليومية", callback_data="daily_reward"),
         InlineKeyboardButton("💸 تحويل الأموال", callback_data="transfer_menu")],
        [InlineKeyboardButton("📈 الاستثمار", callback_data="investment_menu"),
         InlineKeyboardButton("🎮 العودة للألعاب", callback_data="main_menu")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(balance_text, reply_markup=reply_markup, parse_mode='HTML')

@maintenance_check  
@ban_check
async def daily_reward(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """المكافأة اليومية المحسنة"""
    user_id = update.effective_user.id
    user_data = game_bot.get_user_data(user_id)
    
    now = datetime.now()
    last_daily = user_data.get('last_daily')
    
    if last_daily:
        last_daily_date = datetime.fromisoformat(last_daily)
        time_diff = now - last_daily_date
        
        if time_diff.days < 1:
            remaining_time = timedelta(days=1) - time_diff
            hours = remaining_time.seconds // 3600
            minutes = (remaining_time.seconds % 3600) // 60
            await update.message.reply_text(
                f"⏰ <b>المكافأة اليومية</b>\n\n"
                f"عليك الانتظار <b>{hours} ساعة و {minutes} دقيقة</b> للمكافأة التالية!\n\n"
                f"🔥 سلسلتك الحالية: <b>{user_data['daily_streak']} يوم</b>",
                parse_mode='HTML'
            )
            return
        
        # فحص السلسلة
        if time_diff.days == 1:
            user_data['daily_streak'] += 1
        elif time_diff.days > 1:
            user_data['daily_streak'] = 1
    else:
        user_data['daily_streak'] = 1
    
    # حساب المكافأة
    base_reward = random.randint(
        game_bot.settings['daily_reward_min'], 
        game_bot.settings['daily_reward_max']
    )
    
    # مكافأة السلسلة
    streak_bonus = min(user_data['daily_streak'] * 10, 500)  # حد أقصى 500
    
    # مكافأة المستوى
    level_bonus = user_data['level'] * 5
    
    # مكافأة VIP
    vip_bonus = int(base_reward * 0.5) if user_data.get('vip_status') else 0
    
    total_reward = base_reward + streak_bonus + level_bonus + vip_bonus
    
    user_data['balance'] += total_reward
    user_data['last_daily'] = now.isoformat()
    user_data['exp'] += 5
    
    # فحص رفع المستوى
    level_up_msg = ""
    if user_data['exp'] >= game_bot.calculate_level_up_exp(user_data['level']):
        user_data['level'] += 1
        user_data['balance'] += game_bot.settings['level_up_bonus']
        level_up_msg = f"\n🆙 <b>تهانينا! ارتقيت للمستوى {user_data['level']}!</b>\n💰 مكافأة: +{game_bot.settings['level_up_bonus']} كوين"
    
    # فحص الإنجازات
    achievement_msg = game_bot.check_achievements(user_id, user_data)
    
    game_bot.update_user_data(user_id, user_data)
    
    reward_text = f"""
🎁 <b>المكافأة اليومية!</b>

💰 <b>المكافأة الأساسية:</b> {base_reward} كوين
🔥 <b>مكافأة السلسلة ({user_data['daily_streak']} يوم):</b> +{streak_bonus} كوين
🎯 <b>مكافأة المستوى ({user_data['level']}):</b> +{level_bonus} كوين
{'🌟 <b>مكافأة VIP:</b> +' + str(vip_bonus) + ' كوين' if vip_bonus > 0 else ''}

💳 <b>إجمالي المكافأة:</b> {total_reward} كوين
💰 <b>رصيدك الآن:</b> {user_data['balance']:,} كوين

{level_up_msg}
{achievement_msg if achievement_msg else ''}

استمر في الحضور يومياً لزيادة سلسلتك! 🚀
"""
    
    await update.message.reply_text(reward_text, parse_mode='HTML')

# ===== أوامر الإدمن المتقدمة =====

@admin_only
async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """لوحة تحكم المشرف المتقدمة"""
    total_users = len(game_bot.users_data)
    active_users = sum(1 for u in game_bot.users_data.values() if not u.get('is_banned', False))
    banned_users = total_users - active_users
    total_balance = sum(u.get('balance', 0) for u in game_bot.users_data.values())
    total_games = sum(u.get('games_played', 0) for u in game_bot.users_data.values())
    total_messages = sum(u.get('message_count', 0) for u in game_bot.messages_log.values())
    
    admin_text = f"""
👑 <b>لوحة التحكم - الإصدار {BOT_VERSION}</b>

📊 <b>إحصائيات سريعة:</b>
👥 إجمالي المستخدمين: {total_users:,}
✅ المستخدمين النشطين: {active_users:,}
🚫 المستخدمين المحظورين: {banned_users:,}
💰 إجمالي الأموال: {total_balance:,} كوين
🎮 إجمالي الألعاب: {total_games:,}
💬 إجمالي الرسائل: {total_messages:,}

🔧 <b>وضع الصيانة:</b> {'🟢 مفعل' if game_bot.settings['maintenance_mode'] else '🔴 معطل'}

🛠️ <b>الأوامر المتاحة:</b>
/settings - إعدادات البوت
/userinfo <المعرف> - معلومات مستخدم
/usermessages <المعرف> - رسائل المستخدم
/ban <المعرف> <السبب> - حظر مستخدم
/unban <المعرف> - إلغاء حظر
/addmoney <المعرف> <المبلغ> - إضافة أموال
/removemoney <المعرف> <المبلغ> - خصم أموال
/broadcast <الرسالة> - رسالة جماعية
/backup - نسخة احتياطية
/stats_admin - إحصائيات تفصيلية
"""
    
    keyboard = [
        [InlineKeyboardButton("⚙️ الإعدادات", callback_data="admin_settings"),
         InlineKeyboardButton("👥 المستخدمين", callback_data="admin_users")],
        [InlineKeyboardButton("📊 الإحصائيات", callback_data="admin_detailed_stats"),
         InlineKeyboardButton("💰 الاقتصاد", callback_data="admin_economy")],
        [InlineKeyboardButton("📤 رسالة جماعية", callback_data="admin_broadcast"),
         InlineKeyboardButton("💾 نسخ احتياطي", callback_data="admin_backup")],
        [InlineKeyboardButton("🔧 الصيانة", callback_data="admin_maintenance"),
         InlineKeyboardButton("📈 التقارير", callback_data="admin_reports")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(admin_text, reply_markup=reply_markup, parse_mode='HTML')

@admin_only
async def bot_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """إعدادات البوت"""
    if not context.args:
        settings_text = f"""
⚙️ <b>إعدادات البوت:</b>

🔧 <b>وضع الصيانة:</b> {'مفعل' if game_bot.settings['maintenance_mode'] else 'معطل'}
💰 <b>الحد الأدنى للرهان:</b> {game_bot.settings['min_bet']} كوين
💰 <b>الحد الأقصى للرهان:</b> {game_bot.settings['max_bet']:,} كوين
🎁 <b>المكافأة اليومية:</b> {game_bot.settings['daily_reward_min']}-{game_bot.settings['daily_reward_max']} كوين
💳 <b>الرصيد الابتدائي:</b> {game_bot.settings['starting_balance']:,} كوين
🆙 <b>مكافأة رفع المستوى:</b> {game_bot.settings['level_up_bonus']} كوين
💸 <b>رسوم التحويل:</b> {game_bot.settings['transfer_fee']*100:.1f}%
🎉 <b>مكافأة الترحيب:</b> {game_bot.settings['welcome_bonus']} كوين

📝 <b>الاستخدام:</b>
/settings maintenance on/off - تفعيل/إلغاء الصيانة
/settings min_bet <رقم> - تغيير الحد الأدنى
/settings max_bet <رقم> - تغيير الحد الأقصى
/settings daily_min <رقم> - أقل مكافأة يومية
/settings daily_max <رقم> - أكبر مكافأة يومية
"""
        await update.message.reply_text(settings_text, parse_mode='HTML')
        return
    
    setting = context.args[0].lower()
    
    if setting == "maintenance":
        if len(context.args) > 1:
            mode = context.args[1].lower()
            if mode in ['on', 'true', '1', 'نعم']:
                game_bot.settings['maintenance_mode'] = True
                await update.message.reply_text("🔧 تم تفعيل وضع الصيانة!")
            elif mode in ['off', 'false', '0', 'لا']:
                game_bot.settings['maintenance_mode'] = False
                await update.message.reply_text("✅ تم إلغاء وضع الصيانة!")
            game_bot.save_settings()
    
    elif setting == "min_bet" and len(context.args) > 1:
        try:
            new_value = int(context.args[1])
            if new_value > 0:
                game_bot.settings['min_bet'] = new_value
                game_bot.save_settings()
                await update.message.reply_text(f"✅ تم تغيير الحد الأدنى إلى {new_value} كوين")
        except ValueError:
            await update.message.reply_text("❌ قيمة غير صحيحة!")
    
    elif setting == "max_bet" and len(context.args) > 1:
        try:
            new_value = int(context.args[1])
            if new_value > game_bot.settings['min_bet']:
                game_bot.settings['max_bet'] = new_value
                game_bot.save_settings()
                await update.message.reply_text(f"✅ تم تغيير الحد الأقصى إلى {new_value:,} كوين")
        except ValueError:
            await update.message.reply_text("❌ قيمة غير صحيحة!")

@admin_only
async def user_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معلومات مستخدم محسنة"""
    if not context.args:
        await update.message.reply_text("📝 <b>الاستخدام:</b> /userinfo <معرف المستخدم>", parse_mode='HTML')
        return
    
    try:
        user_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("❌ معرف المستخدم يجب أن يكون رقماً!")
        return
    
    user_data = game_bot.get_user_data(user_id)
    message_data = game_bot.messages_log.get(str(user_id), {})
    
    # حساب الإحصائيات المتقدمة
    win_rate = (user_data['wins'] / (user_data['games_played'] or 1)) * 100
    net_profit = user_data['total_won'] - user_data['total_lost']
    
    # حساب آخر نشاط
    last_activity = user_data.get('last_activity')
    if last_activity:
        last_seen = datetime.fromisoformat(last_activity)
        time_since = datetime.now() - last_seen
        if time_since.days > 0:
            activity_text = f"{time_since.days} يوم"
        elif time_since.seconds > 3600:
            activity_text = f"{time_since.seconds // 3600} ساعة"
        else:
            activity_text = f"{time_since.seconds // 60} دقيقة"
    else:
        activity_text = "غير متوفر"
    
    info_text = f"""
👤 <b>معلومات المستخدم: {user_id}</b>

📝 <b>البيانات الشخصية:</b>
• الاسم: {message_data.get('first_name', 'غير متوفر')} {message_data.get('last_name', '')}
• المعرف: @{message_data.get('username', 'غير متوفر')}
• آخر نشاط: منذ {activity_text}
• تاريخ الانضمام: {user_data.get('join_date', 'غير متوفر')[:10]}

💰 <b>المعلومات المالية:</b>
• الرصيد الحالي: {user_data['balance']:,} كوين
• إجمالي الرهان: {user_data['total_wagered']:,} كوين  
• إجمالي الأرباح: {user_data['total_won']:,} كوين
• إجمالي الخسائر: {user_data['total_lost']:,} كوين
• صافي الربح: {net_profit:+,} كوين

🎮 <b>إحصائيات الألعاب:</b>
• المستوى: {user_data['level']} (النقاط: {user_data['exp']:,})
• إجمالي الألعاب: {user_data['games_played']:,}
• الانتصارات: {user_data['wins']:,}
• الخسائر: {user_data['losses']:,}
• معدل الفوز: {win_rate:.2f}%
• اللعبة المفضلة: {user_data.get('favorite_game', 'غير محدد')}

💬 <b>النشاط:</b>
• عدد الرسائل: {message_data.get('message_count', 0):,}
• سلسلة المكافأة: {user_data['daily_streak']} يوم
• عدد الإحالات: {user_data['referral_count']}

🎖️ <b>الحالة:</b>
• العضوية: {'🌟 VIP' if user_data.get('vip_status') else '👤 عادي'}
• الإنجازات: {len(user_data['achievements'])}
• الحالة: {'🚫 محظور' if user_data.get('is_banned') else '✅ نشط'}
"""
    
    if user_data.get('is_banned'):
        info_text += f"\n🚫 <b>معلومات الحظر:</b>\n• السبب: {user_data.get('ban_reason', 'غير محدد')}\n• التاريخ: {user_data.get('ban_date', 'غير محدد')}"
    
    keyboard = [
        [InlineKeyboardButton("💬 الرسائل", callback_data=f"admin_user_messages_{user_id}"),
         InlineKeyboardButton("💰 إدارة المال", callback_data=f"admin_user_money_{user_id}")],
        [InlineKeyboardButton("🚫 حظر/إلغاء حظر", callback_data=f"admin_user_ban_{user_id}"),
         InlineKeyboardButton("⭐ VIP", callback_data=f"admin_user_vip_{user_id}")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(info_text, reply_markup=reply_markup, parse_mode='HTML')

# ===== الألعاب المحسنة =====

@maintenance_check
@ban_check
async def roulette_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """لعبة الروليت المحسنة"""
    user_id = update.effective_user.id
    user_data = game_bot.get_user_data(user_id)
    
    if not context.args or len(context.args) < 2:
        help_text = f"""
🎲 <b>لعبة الروليت الأوروبي</b>

📝 <b>الاستخدام:</b>
/roulette <المبلغ> <الرهان>

💰 <b>حدود الرهان:</b>
الحد الأدنى: {game_bot.settings['min_bet']} كوين
الحد الأقصى: {game_bot.settings['max_bet']:,} كوين

🎯 <b>أنواع الرهانات:</b>
• رقم مباشر (0-36): ربح 35:1
• أحمر/أسود: ربح 1:1
• زوجي/فردي: ربح 1:1
• صف أول (1-12): ربح 2:1
• صف ثاني (13-24): ربح 2:1  
• صف ثالث (25-36): ربح 2:1

مثال: /roulette 100 أحمر
"""
        await update.message.reply_text(help_text, parse_mode='HTML')
        return
    
    try:
        bet_amount = int(context.args[0])
        bet_type = ' '.join(context.args[1:]).lower().strip()
    except ValueError:
        await update.message.reply_text("❌ المبلغ يجب أن يكون رقماً!")
        return
    
    # التحقق من صحة الرهان
    if bet_amount < game_bot.settings['min_bet']:
        await update.message.reply_text(f"❌ الحد الأدنى للرهان {game_bot.settings['min_bet']} كوين!")
        return
    
    if bet_amount > game_bot.settings['max_bet']:
        await update.message.reply_text(f"❌ الحد الأقصى للرهان {game_bot.settings['max_bet']:,} كوين!")
        return
    
    if bet_amount > user_data['balance']:
        await update.message.reply_text(f"❌ رصيدك غير كافي! رصيدك: {user_data['balance']:,} كوين")
        return
    
    # دوران الروليت
    winning_number = random.randint(0, 36)
    red_numbers = {1,3,5,7,9,12,14,16,18,19,21,23,25,27,30,32,34,36}
    
    is_red = winning_number in red_numbers
    is_black = winning_number != 0 and not is_red
    is_even = winning_number != 0 and winning_number % 2 == 0
    is_odd = winning_number != 0 and winning_number % 2 == 1
    
    # تحديد اللون
    if winning_number == 0:
        color = "🟢 أخضر"
    elif is_red:
        color = "🔴 أحمر"
    else:
        color = "⚫ أسود"
    
    # التحقق من الفوز وحساب المضاعف
    won = False
    multiplier = 0
    win_description = ""
    
    # رقم مباشر
    if bet_type.isdigit():
        bet_number = int(bet_type)
        if 0 <= bet_number <= 36 and bet_number == winning_number:
            won = True
            multiplier = 35
            win_description = f"رقم مباشر ({bet_number})"
    
    # الألوان
    elif bet_type in ["أحمر", "red"] and is_red:
        won = True
        multiplier = 1
        win_description = "أحمر"
    elif bet_type in ["أسود", "black"] and is_black:
        won = True
        multiplier = 1  
        win_description = "أسود"
    
    # زوجي/فردي
    elif bet_type in ["زوجي", "even"] and is_even:
        won = True
        multiplier = 1
        win_description = "زوجي"
    elif bet_type in ["فردي", "odd"] and is_odd:
        won = True
        multiplier = 1
        win_description = "فردي"
    
    # الصفوف
    elif bet_type in ["صف أول", "1st", "1-12"] and 1 <= winning_number <= 12:
        won = True
        multiplier = 2
        win_description = "الصف الأول (1-12)"
    elif bet_type in ["صف ثاني", "2nd", "13-24"] and 13 <= winning_number <= 24:
        won = True
        multiplier = 2
        win_description = "الصف الثاني (13-24)"
    elif bet_type in ["صف ثالث", "3rd", "25-36"] and 25 <= winning_number <= 36:
        won = True
        multiplier = 2
        win_description = "الصف الثالث (25-36)"
    
    # تحديث الإحصائيات
    user_data['games_played'] += 1
    user_data['total_wagered'] += bet_amount
    user_data['favorite_game'] = 'roulette'
    
    # حساب النتيجة
    if won:
        winnings = bet_amount * (multiplier + 1)  # المبلغ + الربح
        profit = bet_amount * multiplier
        user_data['balance'] += profit
        user_data['wins'] += 1
        user_data['total_won'] += profit
        user_data['exp'] += min(10 + (multiplier // 5), 50)  # نقاط متغيرة حسب المضاعف
        
        result_text = f"""
🎉 <b>مبروك! فزت في الروليت!</b>

🎲 <b>النتيجة:</b> {winning_number} {color}
🎯 <b>رهانك:</b> {bet_type} ({bet_amount:,} كوين)
✅ <b>الفوز:</b> {win_description}
💰 <b>المضاعف:</b> {multiplier}:1
💵 <b>الربح:</b> {profit:,} كوين
💳 <b>رصيدك:</b> {user_data['balance']:,} كوين
"""
    else:
        user_data['balance'] -= bet_amount
        user_data['losses'] += 1
        user_data['total_lost'] += bet_amount
        user_data['exp'] += 3
        
        result_text = f"""
😔 <b>للأسف! لم تفز هذه المرة</b>

🎲 <b>النتيجة:</b> {winning_number} {color}
🎯 <b>رهانك:</b> {bet_type} ({bet_amount:,} كوين)
❌ <b>خسارة:</b> -{bet_amount:,} كوين
💳 <b>رصيدك:</b> {user_data['balance']:,} كوين
"""
    
    # فحص رفع المستوى
    next_level_exp = game_bot.calculate_level_up_exp(user_data['level'])
    if user_data['exp'] >= next_level_exp:
        old_level = user_data['level']
        user_data['level'] += 1
        level_bonus = game_bot.settings['level_up_bonus']
        user_data['balance'] += level_bonus
        result_text += f"\n🆙 <b>تهانينا! ارتقيت من المستوى {old_level} إلى {user_data['level']}!</b>\n💰 <b>مكافأة:</b> +{level_bonus:,} كوين"
    
    # فحص الإنجازات
    achievement_msg = game_bot.check_achievements(user_id, user_data)
    if achievement_msg:
        result_text += f"\n{achievement_msg}"
    
    game_bot.update_user_data(user_id, user_data)
    
    # إضافة أزرار للعب مرة أخرى
    keyboard = [
        [InlineKeyboardButton("🔄 لعب مرة أخرى", callback_data="game_roulette"),
         InlineKeyboardButton("🎮 ألعاب أخرى", callback_data="main_menu")],
        [InlineKeyboardButton("📊 إحصائياتي", callback_data="show_stats"),
         InlineKeyboardButton("💰 الرصيد", callback_data="show_balance")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(result_text, reply_markup=reply_markup, parse_mode='HTML')

# ===== معالجة الأزرار المحسنة =====

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالج الأزرار المحسن"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    data = query.data
    
    # التحقق من الصيانة والحظر للمستخدمين العاديين
    if not is_admin(user_id):
        if game_bot.is_maintenance_mode():
            await query.edit_message_text(
                f"🔧 {game_bot.settings['maintenance_message']}\nعذراً للإزعاج، سنعود قريباً!"
            )
            return
            
        user_data = game_bot.get_user_data(user_id)
        if user_data.get('is_banned', False):
            await query.edit_message_text(
                f"🚫 تم حظرك من استخدام البوت!\nالسبب: {user_data.get('ban_reason', 'غير محدد')}"
            )
            return
    
    try:
        # الأزرار الرئيسية
        if data == "main_menu":
            await show_main_menu(query)
        elif data == "show_balance":
            await show_balance_inline(query)
        elif data == "show_stats":
            await show_stats_inline(query)
        elif data == "daily_reward":
            await process_daily_reward_inline(query, context)
        elif data == "leaderboard":
            await show_leaderboard(query)
        elif data == "achievements":
            await show_achievements(query)
        elif data == "referral_info":
            await show_referral_info(query)
            
        # أزرار الألعاب
        elif data.startswith("game_"):
            game_type = data.split("_")[1]
            await show_game_info(query, game_type)
            
        # أزرار الإدمن
        elif data.startswith("admin_") and is_admin(user_id):
            await handle_admin_buttons(query, data, context)
            
    except Exception as e:
        logger.error(f"خطأ في معالجة الزر {data}: {e}")
        await query.edit_message_text("❌ حدث خطأ. يرجى المحاولة مرة أخرى.")

async def show_main_menu(query):
    """عرض القائمة الرئيسية"""
    keyboard = [
        [InlineKeyboardButton("🎲 الروليت", callback_data="game_roulette"),
         InlineKeyboardButton("🎰 القمار", callback_data="game_slots")],
        [InlineKeyboardButton("🎯 النرد", callback_data="game_dice"),
         InlineKeyboardButton("🪙 العملة", callback_data="game_coinflip")],
        [InlineKeyboardButton("🃏 البلاك جاك", callback_data="game_blackjack"),
         InlineKeyboardButton("🎫 اليانصيب", callback_data="game_lottery")],
        [InlineKeyboardButton("💰 الرصيد", callback_data="show_balance"),
         InlineKeyboardButton("📊 الإحصائيات", callback_data="show_stats")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text("🎮 اختر لعبة للبدء:", reply_markup=reply_markup)

async def show_balance_inline(query):
    """عرض الرصيد كزر"""
    user_data = game_bot.get_user_data(query.from_user.id)
    balance_text = f"""
💰 <b>رصيدك:</b> {user_data['balance']:,} كوين
🎯 <b>المستوى:</b> {user_data['level']}
⭐ <b>النقاط:</b> {user_data['exp']:,}
🏆 <b>الانتصارات:</b> {user_data['wins']:,}
"""
    
    keyboard = [[InlineKeyboardButton("🔙 العودة", callback_data="main_menu")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(balance_text, reply_markup=reply_markup, parse_mode='HTML')

async def show_game_info(query, game_type):
    """عرض معلومات اللعبة"""
    game_info = {
        "roulette": {
            "name": "🎲 الروليت الأوروبي",
            "description": "ضع رهانك على رقم، لون، أو نمط وادر عجلة الحظ!",
            "command": "/roulette <المبلغ> <الرهان>",
            "example": "/roulette 100 أحمر"
        },
        "slots": {
            "name": "🎰 آلة القمار",
            "description": "ادر البكرات واحصل على مجموعات رابحة!",
            "command": "/slots <المبلغ>",
            "example": "/slots 50"
        },
        "dice": {
            "name": "🎯 لعبة النرد",
            "description": "خمن نتيجة رمي النرد واربح!",
            "command": "/dice <المبلغ> <التخمين 1-6>",
            "example": "/dice 100 4"
        },
        "coinflip": {
            "name": "🪙 قلب العملة",
            "description": "اختر صورة أو كتابة واقلب العملة!",
            "command": "/coinflip <المبلغ> <صورة/كتابة>",
            "example": "/coinflip 200 صورة"
        }
    }
    
    if game_type not in game_info:
        await query.edit_message_text("❌ لعبة غير متوفرة")
        return
    
    game = game_info[game_type]
    info_text = f"""
{game['name']}

📝 <b>الوصف:</b>
{game['description']}

🎮 <b>كيفية اللعب:</b>
<code>{game['command']}</code>

💡 <b>مثال:</b>
<code>{game['example']}</code>

💰 <b>حدود الرهان:</b>
الحد الأدنى: {game_bot.settings['min_bet']} كوين
الحد الأقصى: {game_bot.settings['max_bet']:,} كوين
"""
    
    keyboard = [
        [InlineKeyboardButton("🎮 ألعاب أخرى", callback_data="main_menu"),
         InlineKeyboardButton("💰 رصيدي", callback_data="show_balance")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(info_text, reply_markup=reply_markup, parse_mode='HTML')

def main():
    """تشغيل البوت المحسن"""
    # إنشاء التطبيق
    app = Application.builder().token(BOT_TOKEN).build()
    
    # إضافة معالج الأخطاء
    app.add_error_handler(error_handler)
    
    # إضافة معالج تسجيل الرسائل
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, log_all_messages), group=1)
    
    # الأوامر الأساسية
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("balance", balance))
    app.add_handler(CommandHandler("daily", daily_reward))
    
    # أوامر الإدمن
    app.add_handler(CommandHandler("admin", admin_panel))
    app.add_handler(CommandHandler("settings", bot_settings))
    app.add_handler(CommandHandler("userinfo", user_info))
    
    # أوامر الألعاب
    app.add_handler(CommandHandler("roulette", roulette_game))
    
    # معالج الأزرار
    app.add_handler(CallbackQueryHandler(button_callback))
    
    # تعيين قائمة الأوامر
    commands = [
        BotCommand("start", "بدء استخدام البوت"),
        BotCommand("balance", "عرض الرصيد"),
        BotCommand("daily", "المكافأة اليومية"),
        BotCommand("roulette", "لعبة الروليت"),
        BotCommand("slots", "آلة القمار"),
        BotCommand("dice", "لعبة النرد"),
        BotCommand("coinflip", "قلب العملة"),
        BotCommand("stats", "الإحصائيات"),
        BotCommand("transfer", "تحويل الأموال"),
    ]
    
    # إضافة أوامر الإدمن للمشرفين
    admin_commands = [
        BotCommand("admin", "لوحة تحكم المشرف"),
        BotCommand("settings", "إعدادات البوت"),
        BotCommand("userinfo", "معلومات مستخدم"),
        BotCommand("broadcast", "رسالة جماعية"),
        BotCommand("backup", "نسخة احتياطية")
    ]
    
    async def post_init(app):
        """إعدادات ما بعد التهيئة"""
        try:
            await app.bot.set_my_commands(commands)
            logger.info("تم تعيين قائمة الأوامر بنجاح")
        except Exception as e:
            logger.error(f"فشل في تعيين الأوامر: {e}")
    
    # تعيين callback للتهيئة
    app.post_init = post_init
    
    print("🤖 البوت المطور يعمل الآن...")
    print(f"📱 الإصدار: {BOT_VERSION}")
    print(f"👑 المشرفين: {ADMIN_IDS}")
    print(f"🔧 وضع الصيانة: {'مفعل' if game_bot.is_maintenance_mode() else 'معطل'}")
    print("🎮 الألعاب المتاحة: الروليت، القمار، النرد، قلب العملة")
    print("📊 النظام: تسجيل الرسائل، إدارة المستخدمين، النسخ الاحتياطية")
    print("\n✅ البوت جاهز لاستقبال الرسائل!")
    
    # تشغيل البوت
    app.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)

# ===== باقي الألعاب المحسنة =====

@maintenance_check
@ban_check
async def slots_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """لعبة آلة القمار المحسنة"""
    user_id = update.effective_user.id
    user_data = game_bot.get_user_data(user_id)
    
    if not context.args:
        help_text = f"""
🎰 <b>آلة القمار المتطورة</b>

📝 <b>الاستخدام:</b> /slots <المبلغ>

💰 <b>حدود الرهان:</b>
الحد الأدنى: {game_bot.settings['min_bet']} كوين
الحد الأقصى: {game_bot.settings['max_bet']:,} كوين

🎯 <b>الرموز والمضاعفات:</b>
💎💎💎 - مضاعف x20
7️⃣7️⃣7️⃣ - مضاعف x15
⭐⭐⭐ - مضاعف x10
🍒🍒🍒 - مضاعف x8
🍇🍇🍇 - مضاعف x6
🍊🍊🍊 - مضاعف x5
🍋🍋🍋 - مضاعف x4
رمزان متطابقان - مضاعف x2

مثال: /slots 100
"""
        await update.message.reply_text(help_text, parse_mode='HTML')
        return
    
    try:
        bet_amount = int(context.args[0])
    except ValueError:
        await update.message.reply_text("❌ المبلغ يجب أن يكون رقماً!")
        return
    
    # التحقق من صحة الرهان
    if bet_amount < game_bot.settings['min_bet']:
        await update.message.reply_text(f"❌ الحد الأدنى للرهان {game_bot.settings['min_bet']} كوين!")
        return
    
    if bet_amount > game_bot.settings['max_bet']:
        await update.message.reply_text(f"❌ الحد الأقصى للرهان {game_bot.settings['max_bet']:,} كوين!")
        return
    
    if bet_amount > user_data['balance']:
        await update.message.reply_text(f"❌ رصيدك غير كافي! رصيدك: {user_data['balance']:,} كوين")
        return
    
    # رموز آلة القمار مع أوزان مختلفة
    symbols = [
        ("🍋", 30), ("🍊", 25), ("🍇", 20), ("🍒", 15),
        ("⭐", 8), ("7️⃣", 5), ("💎", 2)
    ]
    
    # إنشاء قائمة موزونة
    weighted_symbols = []
    for symbol, weight in symbols:
        weighted_symbols.extend([symbol] * weight)
    
    # دوران البكرات
    result = [random.choice(weighted_symbols) for _ in range(3)]
    
    # حساب المضاعف
    multiplier = 0
    win_type = ""
    
    if result[0] == result[1] == result[2]:  # ثلاثة متطابقة
        symbol = result[0]
        if symbol == "💎":
            multiplier = 20
            win_type = "💎 JACKPOT! 💎"
        elif symbol == "7️⃣":
            multiplier = 15
            win_type = "🎰 SUPER WIN!"
        elif symbol == "⭐":
            multiplier = 10
            win_type = "⭐ BIG WIN!"
        elif symbol == "🍒":
            multiplier = 8
            win_type = "🍒 GREAT!"
        elif symbol == "🍇":
            multiplier = 6
            win_type = "🍇 GOOD!"
        elif symbol == "🍊":
            multiplier = 5
            win_type = "🍊 NICE!"
        elif symbol == "🍋":
            multiplier = 4
            win_type = "🍋 WIN!"
            
    elif len(set(result)) == 2:  # اثنان متطابقان
        multiplier = 2
        win_type = "✨ PAIR!"
    
    # تحديث الإحصائيات
    user_data['games_played'] += 1
    user_data['total_wagered'] += bet_amount
    user_data['favorite_game'] = 'slots'
    
    if multiplier > 0:
        winnings = bet_amount * multiplier
        profit = winnings - bet_amount
        user_data['balance'] += profit
        user_data['wins'] += 1
        user_data['total_won'] += profit
        user_data['exp'] += min(5 + (multiplier * 2), 50)
        
        # رسالة الفوز مع تأثيرات بصرية
        result_text = f"""
{win_type}

🎰 {'│'.join(result)} 🎰

🎉 <b>فزت بـ {winnings:,} كوين!</b>
💰 <b>الربح:</b> +{profit:,} كوين
🎯 <b>المضاعف:</b> x{multiplier}
💳 <b>رصيدك:</b> {user_data['balance']:,} كوين

{'🎊' * (multiplier // 5)} تهانينا! {'🎊' * (multiplier // 5)}
"""
    else:
        user_data['balance'] -= bet_amount
        user_data['losses'] += 1
        user_data['total_lost'] += bet_amount
        user_data['exp'] += 2
        
        result_text = f"""
🎰 {'│'.join(result)} 🎰

😔 <b>لم تفز هذه المرة</b>
💸 <b>الخسارة:</b> -{bet_amount:,} كوين
💳 <b>رصيدك:</b> {user_data['balance']:,} كوين

حاول مرة أخرى! 🍀
"""
    
    # فحص رفع المستوى
    next_level_exp = game_bot.calculate_level_up_exp(user_data['level'])
    if user_data['exp'] >= next_level_exp:
        old_level = user_data['level']
        user_data['level'] += 1
        level_bonus = game_bot.settings['level_up_bonus']
        user_data['balance'] += level_bonus
        result_text += f"\n🆙 <b>مستوى جديد! {old_level} → {user_data['level']}</b>\n💰 <b>مكافأة:</b> +{level_bonus:,} كوين"
    
    # فحص الإنجازات
    achievement_msg = game_bot.check_achievements(user_id, user_data)
    if achievement_msg:
        result_text += f"\n{achievement_msg}"
    
    game_bot.update_user_data(user_id, user_data)
    
    # أزرار التفاعل
    keyboard = [
        [InlineKeyboardButton("🔄 لعب مرة أخرى", callback_data="game_slots"),
         InlineKeyboardButton("🎮 ألعاب أخرى", callback_data="main_menu")],
        [InlineKeyboardButton("📊 إحصائياتي", callback_data="show_stats"),
         InlineKeyboardButton("💰 الرصيد", callback_data="show_balance")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(result_text, reply_markup=reply_markup, parse_mode='HTML')

@maintenance_check
@ban_check
async def dice_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """لعبة النرد المحسنة"""
    user_id = update.effective_user.id
    user_data = game_bot.get_user_data(user_id)
    
    if not context.args or len(context.args) < 2:
        help_text = f"""
🎯 <b>لعبة النرد المتطورة</b>

📝 <b>الاستخدام:</b> /dice <المبلغ> <التخمين>

🎲 <b>أنواع الرهانات:</b>
• رقم واحد (1-6): ربح x5
• زوجي (2,4,6): ربح x2
• فردي (1,3,5): ربح x2
• صغير (1,2,3): ربح x2
• كبير (4,5,6): ربح x2

💰 <b>حدود الرهان:</b>
الحد الأدنى: {game_bot.settings['min_bet']} كوين
الحد الأقصى: {game_bot.settings['max_bet']:,} كوين

💡 <b>أمثلة:</b>
/dice 100 4 (رقم محدد)
/dice 200 زوجي
/dice 150 كبير
"""
        await update.message.reply_text(help_text, parse_mode='HTML')
        return
    
    try:
        bet_amount = int(context.args[0])
        bet_type = context.args[1].lower().strip()
    except ValueError:
        await update.message.reply_text("❌ المبلغ يجب أن يكون رقماً!")
        return
    
    # التحقق من صحة الرهان
    if bet_amount < game_bot.settings['min_bet']:
        await update.message.reply_text(f"❌ الحد الأدنى للرهان {game_bot.settings['min_bet']} كوين!")
        return
    
    if bet_amount > game_bot.settings['max_bet']:
        await update.message.reply_text(f"❌ الحد الأقصى للرهان {game_bot.settings['max_bet']:,} كوين!")
        return
    
    if bet_amount > user_data['balance']:
        await update.message.reply_text(f"❌ رصيدك غير كافي! رصيدك: {user_data['balance']:,} كوين")
        return
    
    # رمي النرد
    dice_result = random.randint(1, 6)
    dice_emoji = ["", "⚀", "⚁", "⚂", "⚃", "⚄", "⚅"][dice_result]
    
    # تحديد نوع الرهان والفوز
    won = False
    multiplier = 0
    win_description = ""
    
    if bet_type.isdigit():
        guess = int(bet_type)
        if 1 <= guess <= 6 and guess == dice_result:
            won = True
            multiplier = 5
            win_description = f"رقم مباشر ({guess})"
    elif bet_type in ["زوجي", "even"] and dice_result % 2 == 0:
        won = True
        multiplier = 2
        win_description = "زوجي"
    elif bet_type in ["فردي", "odd"] and dice_result % 2 == 1:
        won = True
        multiplier = 2
        win_description = "فردي"
    elif bet_type in ["صغير", "small", "low"] and dice_result <= 3:
        won = True
        multiplier = 2
        win_description = "صغير (1-3)"
    elif bet_type in ["كبير", "big", "high"] and dice_result >= 4:
        won = True
        multiplier = 2
        win_description = "كبير (4-6)"
    
    # تحديث الإحصائيات
    user_data['games_played'] += 1
    user_data['total_wagered'] += bet_amount
    user_data['favorite_game'] = 'dice'
    
    if won:
        winnings = bet_amount * multiplier
        profit = winnings - bet_amount
        user_data['balance'] += profit
        user_data['wins'] += 1
        user_data['total_won'] += profit
        user_data['exp'] += 5 + (multiplier * 3)
        
        result_text = f"""
🎯 <b>تخمين رائع! فزت!</b>

🎲 <b>نتيجة النرد:</b> {dice_result} {dice_emoji}
🎯 <b>رهانك:</b> {bet_type} ({bet_amount:,} كوين)
✅ <b>الفوز:</b> {win_description}
💰 <b>المضاعف:</b> x{multiplier}
💵 <b>الربح:</b> {profit:,} كوين
💳 <b>رصيدك:</b> {user_data['balance']:,} كوين

🎉 أحسنت! استمر في اللعب!
"""
    else:
        user_data['balance'] -= bet_amount
        user_data['losses'] += 1
        user_data['total_lost'] += bet_amount
        user_data['exp'] += 3
        
        result_text = f"""
🎯 <b>للأسف لم تصب هذه المرة</b>

🎲 <b>نتيجة النرد:</b> {dice_result} {dice_emoji}
🎯 <b>رهانك:</b> {bet_type} ({bet_amount:,} كوين)
❌ <b>الخسارة:</b> -{bet_amount:,} كوين
💳 <b>رصيدك:</b> {user_data['balance']:,} كوين

🍀 حظ أوفر في المرة القادمة!
"""
    
    # فحص رفع المستوى والإنجازات
    next_level_exp = game_bot.calculate_level_up_exp(user_data['level'])
    if user_data['exp'] >= next_level_exp:
        old_level = user_data['level']
        user_data['level'] += 1
        level_bonus = game_bot.settings['level_up_bonus']
        user_data['balance'] += level_bonus
        result_text += f"\n🆙 <b>مستوى جديد! {old_level} → {user_data['level']}</b>\n💰 <b>مكافأة:</b> +{level_bonus:,} كوين"
    
    achievement_msg = game_bot.check_achievements(user_id, user_data)
    if achievement_msg:
        result_text += f"\n{achievement_msg}"
    
    game_bot.update_user_data(user_id, user_data)
    
    keyboard = [
        [InlineKeyboardButton("🎲 لعب مرة أخرى", callback_data="game_dice"),
         InlineKeyboardButton("🎮 ألعاب أخرى", callback_data="main_menu")],
        [InlineKeyboardButton("📊 إحصائياتي", callback_data="show_stats"),
         InlineKeyboardButton("💰 الرصيد", callback_data="show_balance")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(result_text, reply_markup=reply_markup, parse_mode='HTML')

@maintenance_check
@ban_check
async def coinflip_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """لعبة قلب العملة المحسنة"""
    user_id = update.effective_user.id
    user_data = game_bot.get_user_data(user_id)
    
    if not context.args or len(context.args) < 2:
        help_text = f"""
🪙 <b>لعبة قلب العملة</b>

📝 <b>الاستخدام:</b> /coinflip <المبلغ> <الاختيار>

🎯 <b>الخيارات:</b>
• صورة - وجه العملة
• كتابة - ظهر العملة
• المضاعف: x2 عند الفوز

💰 <b>حدود الرهان:</b>
الحد الأدنى: {game_bot.settings['min_bet']} كوين
الحد الأقصى: {game_bot.settings['max_bet']:,} كوين

💡 <b>مثال:</b>
/coinflip 100 صورة
/coinflip 250 كتابة
"""
        await update.message.reply_text(help_text, parse_mode='HTML')
        return
    
    try:
        bet_amount = int(context.args[0])
        choice = ' '.join(context.args[1:]).lower().strip()
    except ValueError:
        await update.message.reply_text("❌ المبلغ يجب أن يكون رقماً!")
        return
    
    # التحقق من صحة الرهان
    if bet_amount < game_bot.settings['min_bet']:
        await update.message.reply_text(f"❌ الحد الأدنى للرهان {game_bot.settings['min_bet']} كوين!")
        return
    
    if bet_amount > game_bot.settings['max_bet']:
        await update.message.reply_text(f"❌ الحد الأقصى للرهان {game_bot.settings['max_bet']:,} كوين!")
        return
    
    if bet_amount > user_data['balance']:
        await update.message.reply_text(f"❌ رصيدك غير كافي! رصيدك: {user_data['balance']:,} كوين")
        return
    
    # التحقق من صحة الاختيار
    if choice not in ["صورة", "كتابة", "heads", "tails"]:
        await update.message.reply_text("❌ اختر 'صورة' أو 'كتابة' فقط!")
        return
    
    # تطبيع الاختيار
    if choice in ["heads", "صورة"]:
        choice = "صورة"
    else:
        choice = "كتابة"
    
    # قلب العملة مع تأثير بصري
    flip_animation = ["🪙", "🌀", "💫", "⭐"]
    result = random.choice(["صورة", "كتابة"])
    result_emoji = "🟡" if result == "صورة" else "⚪"
    
    # تحديد الفوز
    won = result == choice
    
    # تحديث الإحصائيات
    user_data['games_played'] += 1
    user_data['total_wagered'] += bet_amount
    user_data['favorite_game'] = 'coinflip'
    
    if won:
        winnings = bet_amount * 2
        profit = bet_amount  # الربح = المبلغ الأصلي
        user_data['balance'] += profit
        user_data['wins'] += 1
        user_data['total_won'] += profit
        user_data['exp'] += 8
        
        result_text = f"""
🎉 <b>رائع! توقعت بشكل صحيح!</b>

🪙 <b>نتيجة العملة:</b> {result} {result_emoji}
🎯 <b>اختيارك:</b> {choice}
✅ <b>صحيح!</b>
💰 <b>الربح:</b> +{profit:,} كوين
💳 <b>رصيدك:</b> {user_data['balance']:,} كوين

🏆 حدس ممتاز! 
"""
    else:
        user_data['balance'] -= bet_amount
        user_data['losses'] += 1
        user_data['total_lost'] += bet_amount
        user_data['exp'] += 3
        
        result_text = f"""
😔 <b>أوه! لم يكن هذا توقعك</b>

🪙 <b>نتيجة العملة:</b> {result} {result_emoji}
🎯 <b>اختيارك:</b> {choice}
❌ <b>خطأ</b>
💸 <b>الخسارة:</b> -{bet_amount:,} كوين
💳 <b>رصيدك:</b> {user_data['balance']:,} كوين

🍀 المرة القادمة ستكون أفضل!
"""
    
    # فحص رفع المستوى والإنجازات
    next_level_exp = game_bot.calculate_level_up_exp(user_data['level'])
    if user_data['exp'] >= next_level_exp:
        old_level = user_data['level']
        user_data['level'] += 1
        level_bonus = game_bot.settings['level_up_bonus']
        user_data['balance'] += level_bonus
        result_text += f"\n🆙 <b>مستوى جديد! {old_level} → {user_data['level']}</b>\n💰 <b>مكافأة:</b> +{level_bonus:,} كوين"
    
    achievement_msg = game_bot.check_achievements(user_id, user_data)
    if achievement_msg:
        result_text += f"\n{achievement_msg}"
    
    game_bot.update_user_data(user_id, user_data)
    
    keyboard = [
        [InlineKeyboardButton("🪙 قلب مرة أخرى", callback_data="game_coinflip"),
         InlineKeyboardButton("🎮 ألعاب أخرى", callback_data="main_menu")],
        [InlineKeyboardButton("📊 إحصائياتي", callback_data="show_stats"),
         InlineKeyboardButton("💰 الرصيد", callback_data="show_balance")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(result_text, reply_markup=reply_markup, parse_mode='HTML')

if __name__ == "__main__":
    main()
