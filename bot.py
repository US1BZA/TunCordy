import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
import json
import datetime
import asyncio
from collections import defaultdict
import logging
from better_profanity import profanity
import re
from languages import LANGUAGES, LANGUAGE_NAMES
import aiofiles
import hashlib
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import hijri_converter

# Загрузка переменных окружения
load_dotenv()

# Получение токена
TOKEN = os.getenv('DISCORD_TOKEN')
if not TOKEN:
    raise ValueError("Токен не найден. Убедитесь, что DISCORD_TOKEN установлен в файле .env")

# Настройка логирования
logging.basicConfig(
    filename='security.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Конфигурация бота
intents = discord.Intents.all()
bot = commands.Bot(command_prefix='!', intents=intents)

# Хранилище настроек сервера
SERVER_SETTINGS_FILE = 'server_settings.json'
server_settings = {}

# Load server settings
def load_server_settings():
    global server_settings
    try:
        with open(SERVER_SETTINGS_FILE, 'r') as f:
            server_settings = json.load(f)
    except FileNotFoundError:
        server_settings = {}

# Save server settings
def save_server_settings():
    with open(SERVER_SETTINGS_FILE, 'w') as f:
        json.dump(server_settings, f)

# Get server language
def get_server_language(guild_id):
    return server_settings.get(str(guild_id), {}).get('language', 'en')

# Server configuration
SERVER_NAME = "CyberTunCompany"

# Multi-language server rules
SERVER_RULES = {
    "en": """📜 **Server Rules**
1. **Respect & Tolerance**
   • No discrimination based on religion, language, race, or ethnicity
   • No hate speech or harassment
   • Respect everyone's personal beliefs and opinions

2. **Content & Behavior**
   • No NSFW content
   • No political discussions
   • No spamming or flooding
   • No advertising without permission
   • No unsolicited DMs to members

3. **Privacy & Security**
   • Do not share personal information
   • Do not record voice channels without permission
   • Do not share harmful files or links

4. **Penalties**
   • First violation: Warning
   • Second violation: 24-hour mute
   • Third violation: 1-week ban
   • Severe violations: Permanent ban

5. **Additional Notes**
   • Moderators have final say in all situations
   • Rules may be updated at any time
   • Being unaware of rules is not an excuse

6. **Language Selection**
   • Only select languages you can actively communicate in
   • Misrepresenting your language abilities is not allowed
   • Language roles will be used for server communications
   • False language claims may result in role removal

🛡️ Breaking these rules may result in immediate action without warning.""",

    "tr": """📜 **Sunucu Kuralları**
1. **Saygı & Hoşgörü**
   • Din, dil, ırk veya etnik köken ayrımcılığı yasaktır
   • Nefret söylemi ve taciz yasaktır
   • Herkesin kişisel inanç ve görüşlerine saygı gösterin

2. **İçerik & Davranış**
   • NSFW içerik yasaktır
   • Siyasi tartışmalar yasaktır
   • Spam veya flood yasaktır
   • İzinsiz reklam yasaktır
   • Üyelere özelden rahatsızlık vermek yasaktır

3. **Gizlilik & Güvenlik**
   • Kişisel bilgi paylaşımı yasaktır
   • İzinsiz ses kaydı almak yasaktır
   • Zararlı dosya veya link paylaşımı yasaktır

4. **Cezalar**
   • İlk ihlal: Uyarı
   • İkinci ihlal: 24 saat susturma
   • Üçüncü ihlal: 1 hafta ban
   • Ağır ihlaller: Kalıcı ban

5. **Ek Notlar**
   • Moderatörlerin kararı kesindir
   • Kurallar herhangi bir zamanda güncellenebilir
   • Kurallardan habersiz olmak mazeret değildir

6. **Dil Seçimi**
   • Yalnızca aktif olarak iletişim kurabildiğiniz dilleri seçin
   • Dil yeteneklerinizi yanlış beyan etmek yasaktır
   • Dil rolleri sunucu iletişiminde kullanılacaktır
   • Yanlış dil beyanı rol kaybına neden olabilir

🛡️ Bu kuralların ihlali anında işlem yapılmasına neden olabilir.""",

    "ru": """📜 **Правила Сервера**
1. **Уважение и Толерантность**
   • Запрещена дискриминация по религии, языку, расе или этнической принадлежности
   • Запрещены язык вражды и домогательства
   • Уважайте личные убеждения и мнения каждого

2. **Контент и Поведение**
   • Запрещен NSFW контент
   • Запрещены политические дискуссии
   • Запрещен спам
   • Запрещена реклама без разрешения
   • Запрещены несанкционированные личные сообщения участникам

3. **Конфиденциальность и Безопасность**
   • Не делитесь личной информацией
   • Не записывайте голосовые каналы без разрешения
   • Не делитесь вредоносными файлами или ссылками

4. **Наказания**
   • Первое нарушение: Предупреждение
   • Второе нарушение: Мут на 24 часа
   • Третье нарушение: Бан на 1 неделю
   • Серьезные нарушения: Перманентный бан

5. **Дополнительные Примечания**
   • Решение модераторов является окончательным
   • Правила могут быть обновлены в любое время
   • Незнание правил не является оправданием

6. **Выбор Языка**
   • Выбирайте только те языки, на которых вы можете активно общаться
   • Искажение языковых способностей запрещено
   • Языковые роли будут использоваться для общения на сервере
   • Ложные заявления о языке могут привести к удалению роли

🛡️ Нарушение этих правил может привести к немедленным действиям без предупреждения.""",

    "ar": """📜 **قوانين السيرفر**
1. **الاحترام والتسامح**
   • يمنع التمييز على أساس الدين أو اللغة أو العرق أو الأصل
   • يمنع خطاب الكراهية والتحرش
   • احترم المعتقدات والآراء الشخصية للجميع

2. **المحتوى والسلوك**
   • يمنع المحتوى غير اللائق
   • يمنع النقاش السياسي
   • يمنع السبام والفلود
   • يمنع الإعلان بدون إذن
   • يمنع إزعاج الأعضاء في الخاص

3. **الخصوصية والأمان**
   • لا تشارك المعلومات الشخصية
   • لا تسجل القنوات الصوتية بدون إذن
   • لا تشارك الملفات أو الروابط الضارة

4. **العقوبات**
   • المخالفة الأولى: تحذير
   • المخالفة الثانية: كتم لمدة 24 ساعة
   • المخالفة الثالثة: حظر لمدة أسبوع
   • المخالفات الخطيرة: حظر دائم

5. **ملاحظات إضافية**
   • قرار المشرفين نهائي
   • يمكن تحديث القوانين في أي وقت
   • عدم معرفة القوانين ليس عذراً

6. **اختيار اللغة**
   • اختر فقط اللغات التي يمكنك التواصل بها بنشاط
   • لا يُسمح بالتحريف في قدراتك اللغوية
   • سيتم استخدام أدوار اللغة للتواصل في السيرفر
   • قد يؤدي الادعاء الكاذب باللغة إلى إزالة الدور

🛡️ مخالفة هذه القوانين قد تؤدي إلى إجراءات فورية بدون تحذير.""",

    "az": """📜 **Server Qaydaları**
1. **Dil Seçimi**
   • Yalnız aktiv ünsiyyət qura bildiyiniz dilləri seçin
   • Dil qabiliyyətlərinizi yanlış təqdim etmək qadağandır
   • Dil rolları server ünsiyyətində istifadə olunacaq
   • Yanlış dil iddiası rolun ləğvinə səbəb ola bilər

2. **İçerik & Davranış**
   • NSFW içerik yasaktır
   • Siyasi tartışmalar yasaktır
   • Spam veya flood yasaktır
   • İzinsiz reklam yasaktır
   • Üyelere özelden rahatsızlık vermek yasaktır

3. **Gizlilik & Güvenlik**
   • Kişisel bilgi paylaşımı yasaktır
   • İzinsiz ses kaydı almak yasaktır
   • Zararlı dosya veya link paylaşımı yasaktır

4. **Cezalar**
   • İlk ihlal: Uyarı
   • İkinci ihlal: 24 saat susturma
   • Üçüncü ihlal: 1 hafta ban
   • Ağır ihlaller: Kalıcı ban

5. **Ek Notlar**
   • Moderatörlerin kararı kesindir
   • Kurallar herhangi bir zamanda güncellenebilir
   • Kurallardan habersiz olmak mazeret değildir

6. **اختيار اللغة**
   • اختر فقط اللغات التي يمكنك التواصل بها بنشاط
   • لا يُسمح بالتحريف في قدراتك اللغوية
   • سيتم استخدام أدوار اللغة للتواصل في السيرفر
   • قد يؤدي الادعاء الكاذب باللغة إلى إزالة الدور

🛡️ بۇ قائىدىلەرنى بۇزۇش دەرھال مۇئامىلىگە ئېلىنىشى مۇمكىن."""
}

# Bot commands help messages
BOT_COMMANDS_HELP = {
    "en": """🤖 **Bot Commands**
1. **General Commands**
   • `!help` - Show this help message
   • `!language [en/tr/ru/ar/az/ug]` - Change your language
   • `!myroles` - View your roles

2. **Role Commands**
   • `!giverole [role_name] [language_code]` - Get a special role in your language
   Available roles: tcf

3. **Personal Notes (DM Only)**
   • `!id` - Get your personal ID
   • `!note [content]` - Add a new personal note
   • `!notes` - View all your notes
   • `!clear_notes` - Delete all your notes

4. **Admin Commands**
   • `!setup` - Setup server channels and roles
   • `!purge_channels` - Delete all channels (Owner only)

⚠️ Use commands responsibly and follow server rules!""",

    "tr": """🤖 **Bot Komutları**
1. **Genel Komutlar**
   • `!help` - Bu yardım mesajını göster
   • `!language [en/tr/ru/ar/az/ug]` - Dilinizi değiştirin
   • `!myroles` - Rollerinizi görüntüleyin

2. **Rol Komutları**
   • `!giverole [rol_adı] [dil_kodu]` - Kendi dilinizde özel rol alın
   Mevcut roller: tcf

3. **Kişisel Notlar (Sadece DM)**
   • `!id` - Kişisel ID'nizi alın
   • `!note [içerik]` - Yeni not ekleyin
   • `!notes` - Tüm notlarınızı görüntüleyin
   • `!clear_notes` - Tüm notlarınızı silin

4. **Yönetici Komutları**
   • `!setup` - Sunucu kanallarını ve rollerini kur
   • `!purge_channels` - Tüm kanalları sil (Sadece sahip)

⚠️ Komutları sorumlu kullanın ve sunucu kurallarına uyun!""",

    "ru": """🤖 **Команды Бота**
1. **Общие Команды**
   • `!help` - Показать это сообщение
   • `!language [en/tr/ru/ar/az/ug]` - Изменить язык
   • `!myroles` - Просмотр ваших ролей

2. **Команды Ролей**
   • `!giverole [имя_роли] [код_языка]` - Получить особую роль на вашем языке
   Доступные роли: tcf

3. **Личные Заметки (Только в ЛС)**
   • `!id` - Получить ваш ID
   • `!note [содержание]` - Добавить заметку
   • `!notes` - Просмотреть все заметки
   • `!clear_notes` - Удалить все заметки

4. **Команды Администратора**
   • `!setup` - Настройка каналов и ролей
   • `!purge_channels` - Удалить все каналы (Только владелец)

⚠️ Используйте команды ответственно и следуйте правилам сервера!""",

    "ar": """🤖 **أوامر البوت**
1. **الأوامر العامة**
   • `!help` - عرض رسالة المساعدة هذه
   • `!language [en/tr/ru/ar/az/ug]` - تغيير لغتك
   • `!myroles` - عرض أدوارك

2. **أوامر الأدوار**
   • `!giverole [اسم_الدور] [رمز_اللغة]` - احصل على دور خاص بلغتك
   الأدوار المتاحة: tcf

3. **الملاحظات الشخصية (الرسائل الخاصة فقط)**
   • `!id` - احصل على معرفك الشخصي
   • `!note [المحتوى]` - إضافة ملاحظة جديدة
   • `!notes` - عرض جميع ملاحظاتك
   • `!clear_notes` - حذف جميع ملاحظاتك

4. **أوامر المشرف**
   • `!setup` - إعداد قنوات وأدوار السيرفر
   • `!purge_channels` - حذف جميع القنوات (المالك فقط)

⚠️ استخدم الأوامر بمسؤولية واتبع قواعد السيرفر!"""
}

# Update categories to include rules and bot-commands
CATEGORIES = {
    "📢 Information": [
        "📜-rules",
        "🤖-bot-commands",
        "🎉-welcome",
        "📢-announcements",
        "🔊 Announcements Voice"
    ],
    
    "🎓 Academic Discussions": [
        "🕌-religion-studies",
        "📜-history-studies",
        "🎭-philosophy-studies",
        "📚-literature-studies",
        "🗣️-political-science",
        "🧠-sociology-studies",
        "🔊 Academic Voice Hall",
        "🔊 Study Room (8 users)",
        "🔊 Duo Study Room (2 users)",
        "🔊 Squad Study Room (4 users)",
        "🔊 Team Study Room (6 users)"
    ],

    "🛡️ Cybersecurity": [
        "📢-announcements",
        "🎯-ctf-events",
        "💡-tips",
        "🔧-tools",
        "📚-resources",
        "🔊 CTF Voice (8 users)",
        "🔊 Team Alpha (8 users)",
        "🔊 Team Beta (8 users)",
        "🔊 Team Gamma (8 users)"
    ],
    
    "📚 Education Areas": [
        "🔰-beginner-level",
        "🎓-intermediate-level",
        "🎯-advanced-level",
        "📝-study-notes",
        "📹-video-lessons",
        "🔊 Training Room (8 users)",
        "🔊 Mentor Room (8 users)"
    ],
    
    "🎯 Practice Areas": [
        "🔒-vulnhub",
        "🎯-hackthebox",
        "🌐-tryhackme",
        "🛡️-portswigger",
        "💻-hack-the-games",
        "🔊 Practice Voice (8 users)",
        "🔊 Team Practice (8 users)"
    ],
    
    "🔒 Security Areas": [
        "🌐-web-security",
        "🖥️-system-security",
        "📱-mobile-security",
        "🔐-cryptography",
        "🕵️-osint",
        "🌍-network-security",
        "☁️-cloud-security",
        "🔊 Security Meeting (8 users)",
        "🔊 Red Team (8 users)",
        "🔊 Blue Team (8 users)"
    ],
    
    "💻 Laboratory": [
        "🎯-ctf-solutions",
        "🔬-malware-analysis",
        "🛠️-tool-development",
        "📝-notes",
        "🧪-lab-environment",
        "🔊 Lab Voice (8 users)",
        "🔊 Research Room (8 users)"
    ],
    
    "🛠️ Tools and Resources": [
        "🔧-tool-sharing",
        "📚-document-archive",
        "🔗-useful-links",
        "💡-script-sharing",
        "📖-cheatsheets",
        "🔊 Tool Workshop (8 users)",
        "🔊 Development Room (8 users)"
    ],
    
    "🤝 Community": [
        "💬-chat",
        "❓-questions",
        "🤝-help",
        "🎉-achievements",
        "📣-announcements",
        "🎪-events",
        "🔊 Public Lounge (8 users)",
        "🔊 Community Chat (8 users)",
        "🔊 Gaming Voice (8 users)",
        "🔊 Music Room (8 users)"
    ],
    
    "🛡️ Security": [
        "🔒-security-logs",
        "⚠️-alerts",
        "🛡️-audit-logs",
        "🚫-banned-users",
        "🔊 Admin Voice (8 users)",
        "🔊 Mod Voice (8 users)",
        "🔊 Emergency Meeting (8 users)"
    ]
}

# Roles with specific permissions and colors
ROLES = [
    # Administrative Roles
    {"name": "👑 Owner", "color": discord.Color.dark_red(), "permissions": discord.Permissions.all()},
    {"name": "🛡️ Admin", "color": discord.Color.red(), "permissions": discord.Permissions.all()},
    {"name": "🛡️ Moderator", "color": discord.Color.blue(), "permissions": discord.Permissions(manage_messages=True, kick_members=True)},
    
    # Teaching Staff
    {"name": "👨‍🏫 Head Instructor", "color": discord.Color.purple(), "permissions": discord.Permissions(manage_messages=True)},
    {"name": "👨‍🏫 Senior Instructor", "color": discord.Color.dark_purple(), "permissions": discord.Permissions(manage_messages=True)},
    {"name": "👨‍🏫 Instructor", "color": discord.Color.magenta(), "permissions": discord.Permissions(manage_messages=True)},
    
    # Technical Roles
    {"name": "🐧 Linux Expert", "color": discord.Color.orange()},
    {"name": "💻 System Administrator", "color": discord.Color.dark_gold()},
    {"name": "🌐 Network Specialist", "color": discord.Color.teal()},
    {"name": "🔒 Security Researcher", "color": discord.Color.dark_teal()},
    {"name": "🕵️ OSINT Specialist", "color": discord.Color.dark_blue()},
    {"name": "🦠 Malware Analyst", "color": discord.Color.dark_orange()},
    {"name": "🔍 Forensics Expert", "color": discord.Color.dark_purple()},
    {"name": "🌐 Web Security Expert", "color": discord.Color.blue()},
    {"name": "📱 Mobile Security Expert", "color": discord.Color.green()},
    {"name": "☁️ Cloud Security Expert", "color": discord.Color.light_grey()},
    {"name": "🛠️ Tool Developer", "color": discord.Color.dark_grey()},
    {"name": "🎯 CTF Player", "color": discord.Color.green()},
    {"name": "💻 Pentester", "color": discord.Color.dark_purple()},
    
    # Level Roles
    {"name": "🎓 Expert", "color": discord.Color.dark_red()},
    {"name": "🎯 Advanced", "color": discord.Color.dark_gold()},
    {"name": "🎓 Intermediate", "color": discord.Color.gold()},
    {"name": "🔰 Beginner", "color": discord.Color.dark_grey()},
    
    # Special Roles
    {"name": "🏆 Contest Winner", "color": discord.Color.gold()},
    {"name": "🌟 VIP Member", "color": discord.Color.purple()},
    {"name": "💎 Active Contributor", "color": discord.Color.blue()}
]

# Anti-raid protection
class AntiRaid:
    def __init__(self):
        self.ban_count = defaultdict(lambda: {"count": 0, "last_reset": datetime.datetime.now()})
        self.max_bans = 3  # Maximum bans allowed in time window
        self.time_window = 10  # Time window in seconds
        self.banned_users = set()

    def can_ban(self, admin_id):
        now = datetime.datetime.now()
        admin_data = self.ban_count[admin_id]
        
        # Reset counter if time window has passed
        if (now - admin_data["last_reset"]).seconds > self.time_window:
            admin_data["count"] = 0
            admin_data["last_reset"] = now
        
        # Check if admin has exceeded ban limit
        if admin_data["count"] >= self.max_bans:
            return False
        
        admin_data["count"] += 1
        return True

anti_raid = AntiRaid()

# Security logging
async def log_security_event(guild, user, event_type, details):
    log_entry = {
        "timestamp": datetime.datetime.now().isoformat(),
        "guild_id": guild.id,
        "guild_name": guild.name,
        "user_id": user.id,
        "user_name": str(user),
        "event_type": event_type,
        "details": details
    }
    
    logging.info(json.dumps(log_entry))
    
    # Create logs channel if it doesn't exist
    logs_channel = discord.utils.get(guild.channels, name="🔒-security-logs")
    if not logs_channel:
        category = discord.utils.get(guild.categories, name="🛡️ Cybersecurity")
        if not category:
            category = await guild.create_category("🛡️ Cybersecurity")
        logs_channel = await guild.create_text_channel("🔒-security-logs", category=category)

    embed = discord.Embed(
        title=f"Security Event: {event_type}",
        description=f"Details: {details}",
        color=discord.Color.red()
    )
    embed.add_field(name="User", value=str(user))
    embed.add_field(name="User ID", value=user.id)
    embed.add_field(name="Timestamp", value=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    
    await logs_channel.send(embed=embed)

# Load profanity words in multiple languages
PROFANITY_PATTERNS = {
    'en': profanity.load_censor_words(),
    'tr': [
        # Turkish profanity words will be loaded from a file
    ],
    # Add other languages as needed
}

# Personal notes encryption
class NotesEncryption:
    def __init__(self):
        self.keys = {}

    def get_user_key(self, user_id: int) -> bytes:
        if user_id not in self.keys:
            # Generate a unique key for each user based on their ID
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=str(user_id).encode(),
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(str(user_id).encode()))
            self.keys[user_id] = Fernet(key)
        return self.keys[user_id]

    def encrypt_note(self, user_id: int, content: str) -> str:
        key = self.get_user_key(user_id)
        return key.encrypt(content.encode()).decode()

    def decrypt_note(self, user_id: int, encrypted_content: str) -> str:
        key = self.get_user_key(user_id)
        return key.decrypt(encrypted_content.encode()).decode()

notes_crypto = NotesEncryption()

# Personal notes storage
NOTES_DIR = 'user_notes'
os.makedirs(NOTES_DIR, exist_ok=True)

async def save_note(user_id: int, note_content: str):
    encrypted_content = notes_crypto.encrypt_note(user_id, note_content)
    async with aiofiles.open(f'{NOTES_DIR}/{user_id}_notes.enc', 'a') as f:
        await f.write(encrypted_content + '\n')

async def get_notes(user_id: int) -> list:
    try:
        async with aiofiles.open(f'{NOTES_DIR}/{user_id}_notes.enc', 'r') as f:
            content = await f.read()
            notes = []
            for note in content.strip().split('\n'):
                if note:
                    try:
                        decrypted = notes_crypto.decrypt_note(user_id, note)
                        notes.append(decrypted)
                    except:
                        continue
            return notes
    except FileNotFoundError:
        return []

# Server configuration
SERVER_NAME = "CyberTunCompany"

# Role translations
ROLE_TRANSLATIONS = {
    "tcf": {
        "en": "🏆 TCF Champion",
        "tr": "🏆 TCF Şampiyonu",
        "ru": "🏆 Чемпион TCF",
        "ar": "🏆 بطل TCF",
        "az": "🏆 TCF Çempionu",
        "ug": "🏆 TCF چېمپىيونى"
    },
    # Add other role translations here
}

# Track assigned roles
ASSIGNED_ROLES = defaultdict(set)  # role_name -> set of user_ids

# Add language roles
LANGUAGE_ROLES = {
    "en": "🇬🇧 English Speaker",
    "tr": "🇹🇷 Türkçe Konuşan",
    "ru": "🇷🇺 Русскоговорящий",
    "ar": "🇸🇦 متحدث العربية",
    "az": "🇦🇿 Azərbaycan dilli",
    "ug": "🔵 ئۇيغۇرچە سۆزلىگۈچى"
}

# Special dates and events
ISLAMIC_SPECIAL_DATES = {
    "ramazan_baslangic": {
        "tr": "Ramazan ayı başlangıcı. Hayırlı Ramazanlar! 🌙",
        "en": "Beginning of Ramadan. Ramadan Mubarak! 🌙",
        "ru": "Начало месяца Рамадан. Рамадан Мубарак! 🌙",
        "ar": "بداية شهر رمضان. رمضان مبارك! 🌙",
        "az": "Ramazan ayının başlanğıcı. Ramazan mübarək! 🌙",
        "ug": "رامىزان ئېيىنىڭ باشلىنىشى. رامىزان مۇبارەك! 🌙"
    },
    "ramazan_bayrami": {
        "tr": "Ramazan Bayramınız mübarek olsun! 🎉",
        "en": "Eid Mubarak! Happy Eid al-Fitr! 🎉",
        "ru": "Ид Мубарак! С праздником Ураза-байрам! 🎉",
        "ar": "عيد مبارك! عيد الفطر السعيد! 🎉",
        "az": "Ramazan bayramınız mübarək! 🎉",
        "ug": "روزا ھېيتىڭىزغا مۇبارەك بولسۇن! 🎉"
    },
    "kurban_bayrami": {
        "tr": "Kurban Bayramınız mübarek olsun! 🎊",
        "en": "Happy Eid al-Adha! 🎊",
        "ru": "С праздником Курбан-байрам! 🎊",
        "ar": "عيد الأضحى المبارك! 🎊",
        "az": "Qurban bayramınız mübarək! 🎊",
        "ug": "قۇربان ھېيتىڭىزغا مۇبارەك بولسۇن! 🎊"
    },
    "mevlid_kandili": {
        "tr": "Mevlid Kandiliniz mübarek olsun! 🕌",
        "en": "Happy Mawlid al-Nabi! 🕌",
        "ru": "С праздником Мавлид ан-Наби! 🕌",
        "ar": "المولد النبوي الشريف! 🕌",
        "az": "Mövlud Qəndiliniz mübarək! 🕌",
        "ug": "مەۋلۇت قەندىلىڭىزگە مۇبارەك بولسۇن! 🕌"
    },
    "regaip_kandili": {
        "tr": "Regaip Kandiliniz mübarek olsun! 🕯️",
        "en": "Happy Laylat al-Raghaib! 🕯️",
        "ru": "Благословенная ночь Рагаиб! 🕯️",
        "ar": "ليلة الرغائب مباركة! 🕯️",
        "az": "Rəğaib Qəndiliniz mübarək! 🕯️",
        "ug": "رەغايىب قەندىلىڭىزگە مۇبارەك بولسۇن! 🕯️"
    },
    "mirac_kandili": {
        "tr": "Mirac Kandiliniz mübarek olsun! ✨",
        "en": "Happy Laylat al-Miraj! ✨",
        "ru": "Благословенная ночь Мирадж! ✨",
        "ar": "ليلة المعراج مباركة! ✨",
        "az": "Merac Qəndiliniz mübarək! ✨",
        "ug": "مېراج قەندىلىڭىزگە مۇبارەك بولسۇن! ✨"
    },
    "berat_kandili": {
        "tr": "Berat Kandiliniz mübarek olsun! 🌟",
        "en": "Happy Laylat al-Bara'at! 🌟",
        "ru": "Благословенная ночь Бараат! 🌟",
        "ar": "ليلة البراءة مباركة! 🌟",
        "az": "Bərat Qəndiliniz mübarək! 🌟",
        "ug": "بەرائەت قەندىلىڭىزگە مۇبارەك بولسۇن! 🌟"
    },
    "kadir_gecesi": {
        "tr": "Kadir Geceniz mübarek olsun! 🌙✨",
        "en": "Happy Laylat al-Qadr! 🌙✨",
        "ru": "Благословенная Ночь Предопределения! 🌙✨",
        "ar": "ليلة القدر مباركة! 🌙✨",
        "az": "Qədr Gecəniz mübarək! 🌙✨",
        "ug": "قەدىر كېچىڭىزگە مۇبارەك بولسۇن! 🌙✨"
    }
}

CYBERSECURITY_SPECIAL_DATES = {
    # Önemli Siber Güvenlik Günleri
    "data_privacy_day": {
        "date": "01-28",
        "tr": "Veri Gizliliği Günü 🔒\nVeri güvenliğinin önemini hatırlayalım!",
        "en": "Data Privacy Day 🔒\nLet's remember the importance of data security!",
        "ru": "День защиты персональных данных 🔒\nДавайте помнить о важности безопасности данных!"
    },
    "safer_internet_day": {
        "date": "02-07",
        "tr": "Güvenli İnternet Günü 🌐\nDaha güvenli bir internet için farkındalık günü!",
        "en": "Safer Internet Day 🌐\nAwareness day for a safer internet!",
        "ru": "День безопасного интернета 🌐\nДень повышения осведомленности о безопасности в интернете!"
    },
    "world_backup_day": {
        "date": "03-31",
        "tr": "Dünya Yedekleme Günü 💾\nVerilerinizi düzenli yedeklemeyi unutmayın!",
        "en": "World Backup Day 💾\nDon't forget to regularly backup your data!",
        "ru": "Всемирный день резервного копирования 💾\nНе забывайте регулярно создавать резервные копии данных!"
    },
    
    # Siber Güvenlik Alanında Önemli İsimler ve Anma Tarihleri
    "alan_turing": {
        "date": "06-23",
        "tr": "Alan Turing'in ölüm yıldönümü (1954) 💻\nModern bilgisayar biliminin öncüsü.",
        "en": "Death anniversary of Alan Turing (1954) 💻\nPioneer of modern computer science.",
        "ru": "Годовщина смерти Алана Тьюринга (1954) 💻\nПионер современной информатики."
    },
    "aaron_swartz": {
        "date": "01-11",
        "tr": "Aaron Swartz'ın ölüm yıldönümü (2013) 🌟\nİnternet aktivisti ve Reddit'in kurucu ortağı.",
        "en": "Death anniversary of Aaron Swartz (2013) 🌟\nInternet activist and Reddit co-founder.",
        "ru": "Годовщина смерти Аарона Шварца (2013) 🌟\nИнтернет-активист и сооснователь Reddit."
    },
    "kevin_mitnick": {
        "date": "07-16",
        "tr": "Kevin Mitnick'in ölüm yıldönümü (2023) 🎯\nEfsanevi siber güvenlik uzmanı.",
        "en": "Death anniversary of Kevin Mitnick (2023) 🎯\nLegendary cybersecurity expert.",
        "ru": "Годовщина смерти Кевина Митника (2023) 🎯\nЛегендарный эксперт по кибербезопасности."
    }
}

async def get_hijri_date():
    """Güncel Hicri tarihi döndüren fonksiyon"""
    today = datetime.date.today()
    hijri = hijri_converter.Gregorian(today.year, today.month, today.day).to_hijri()
    return hijri

async def check_islamic_special_dates():
    """İslami özel günleri kontrol eden fonksiyon"""
    hijri_date = await get_hijri_date()
    
    # Ramazan başlangıcı (1 Ramazan)
    if hijri_date.month == 9 and hijri_date.day == 1:
        return "ramazan_baslangic"
    
    # Ramazan Bayramı (1 Şevval)
    elif hijri_date.month == 10 and hijri_date.day == 1:
        return "ramazan_bayrami"
    
    # Kurban Bayramı (10 Zilhicce)
    elif hijri_date.month == 12 and hijri_date.day == 10:
        return "kurban_bayrami"
    
    # Mevlid Kandili (12 Rebiülevvel)
    elif hijri_date.month == 3 and hijri_date.day == 12:
        return "mevlid_kandili"
    
    # Regaip Kandili (Recep ayının ilk Perşembe gecesi)
    elif hijri_date.month == 7 and hijri_date.day == 1:  # Yaklaşık tarih
        return "regaip_kandili"
    
    # Miraç Kandili (27 Recep)
    elif hijri_date.month == 7 and hijri_date.day == 27:
        return "mirac_kandili"
    
    # Berat Kandili (15 Şaban)
    elif hijri_date.month == 8 and hijri_date.day == 15:
        return "berat_kandili"
    
    # Kadir Gecesi (27 Ramazan)
    elif hijri_date.month == 9 and hijri_date.day == 27:
        return "kadir_gecesi"
    
    return None

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}!')
    load_server_settings()
    
    # Özel tarih kontrolünü başlat
    bot.loop.create_task(check_special_dates())

async def check_special_dates():
    """Her gün özel tarihleri kontrol eden ve mesaj gönderen fonksiyon"""
    while True:
        now = datetime.datetime.now()
        current_date = now.strftime("%m-%d")
        
        # İslami özel günler kontrolü
        islamic_special_day = await check_islamic_special_dates()
        if islamic_special_day:
            for guild in bot.guilds:
                announcements_channel = discord.utils.get(guild.channels, name="📢-announcements")
                if announcements_channel:
                    lang = get_server_language(guild.id)
                    message = ISLAMIC_SPECIAL_DATES[islamic_special_day].get(lang, 
                             ISLAMIC_SPECIAL_DATES[islamic_special_day]["en"])
                    
                    embed = discord.Embed(
                        title="🕌 İslami Özel Gün | Islamic Special Day",
                        description=message,
                        color=discord.Color.green()
                    )
                    await announcements_channel.send(embed=embed)
        
        # Siber güvenlik özel günleri ve anma tarihleri kontrolü
        for event_name, event_info in CYBERSECURITY_SPECIAL_DATES.items():
            if event_info["date"] == current_date:
                for guild in bot.guilds:
                    announcements_channel = discord.utils.get(guild.channels, name="📢-announcements")
                    if announcements_channel:
                        lang = get_server_language(guild.id)
                        message = event_info.get(lang, event_info["en"])
                        
                        embed = discord.Embed(
                            title="🔒 Siber Güvenlik Özel Günü | Cybersecurity Special Day",
                            description=message,
                            color=discord.Color.blue()
                        )
                        await announcements_channel.send(embed=embed)
        
        # 24 saat bekle
        await asyncio.sleep(86400)  # 24 saat = 86400 saniye

@bot.event
async def on_guild_join(guild):
    # Set default language to English
    server_settings[str(guild.id)] = {'language': 'en'}
    save_server_settings()
    
    # Set server name
    try:
        await guild.edit(name=SERVER_NAME)
    except discord.Forbidden:
        print(f"Could not set server name to {SERVER_NAME}")
    
    # Start server setup
    await setup_server(guild)

async def setup_server(guild):
    # Only proceed if the command was initiated by the server owner
    if not guild.owner:
        return
        
    # Create categories and channels
    for category_name, channels in CATEGORIES.items():
        category = await guild.create_category(category_name)
        
        # Create channels for each category
        for channel_name in channels:
            channel = await guild.create_text_channel(channel_name, category=category)
            
            # Post rules in rules channel
            if channel_name == "📜-rules":
                # First, send language selection message
                language_select = discord.Embed(
                    title="Select Your Language | Dilinizi Seçin | Выберите язык | اختر لغتك | Dilini Seç | تىلىڭىزنى تاللاڭ",
                    description="Click on your preferred language to read the rules:\n\n" +
                              "🇬🇧 English\n" +
                              "🇹🇷 Türkçe\n" +
                              "🇷🇺 Русский\n" +
                              "🇸🇦 العربية\n" +
                              "🇦🇿 Azərbaycan\n" +
                              "🔵 ئۇيغۇرچە",
                    color=discord.Color.blue()
                )
                msg = await channel.send(embed=language_select)
                
                # Add language selection reactions
                await msg.add_reaction("🇬🇧")  # English
                await msg.add_reaction("🇹🇷")  # Turkish
                await msg.add_reaction("🇷🇺")  # Russian
                await msg.add_reaction("🇸🇦")  # Arabic
                await msg.add_reaction("🇦🇿")  # Azerbaijani
                await msg.add_reaction("🔵")  # Uyghur
            
            # Post commands help in bot-commands channel
            elif channel_name == "🤖-bot-commands":
                for lang_code, commands_help in BOT_COMMANDS_HELP.items():
                    await channel.send(f"**[{lang_code.upper()}]**")
                    await channel.send(commands_help)
                    await channel.send("─" * 40)  # Separator

    # Create roles
    for role_info in ROLES:
        await guild.create_role(
            name=role_info["name"],
            color=role_info["color"],
            permissions=role_info.get("permissions", discord.Permissions.none())
        )

    # Welcome message
    system_channel = await guild.create_text_channel("🎉-welcome")
    lang = get_server_language(guild.id)
    await system_channel.send(LANGUAGES[lang].MESSAGES["welcome"])

# Add reaction handler for rules
@bot.event
async def on_raw_reaction_add(payload):
    if payload.member.bot:
        return

    channel = bot.get_channel(payload.channel_id)
    if channel and channel.name == "📜-rules":
        message = await channel.fetch_message(payload.message_id)
        
        # Language selection reactions
        emoji_to_lang = {
            "🇬🇧": "en",
            "🇹🇷": "tr",
            "🇷🇺": "ru",
            "🇸🇦": "ar",
            "🇦🇿": "az",
            "🔵": "ug"
        }
        
        if str(payload.emoji) in emoji_to_lang:
            lang = emoji_to_lang[str(payload.emoji)]
            
            # Create embed for rules in selected language
            rules_embed = discord.Embed(
                title=f"Server Rules | Sunucu Kuralları | Правила Сервера | قوانين السيرفر | Server Qaydaları | مۇلازىمېتىر قائىدىلىرى",
                description=SERVER_RULES[lang],
                color=discord.Color.green()
            )
            
            # Send rules
            await channel.send(embed=rules_embed)
            
            # Add accept button
            accept_button = discord.ui.Button(
                style=discord.ButtonStyle.success,
                label="I Accept the Rules | Kuralları Kabul Ediyorum | Я принимаю правила | أوافق على القواعد | Qaydaları Qəbul Edirəm | قائىدىلەرنى قوبۇل قىلىمەن",
                custom_id=f"accept_rules_{lang}"
            )
            
            view = discord.ui.View()
            view.add_item(accept_button)
            await channel.send(view=view)
            
            # Remove user's reaction
            await message.remove_reaction(payload.emoji, payload.member)

@bot.event
async def on_interaction(interaction):
    if interaction.type == discord.InteractionType.component:
        if interaction.custom_id.startswith("accept_rules_"):
            # Get the language from custom_id
            lang = interaction.custom_id.split("_")[2]
            
            # Add member role and language role
            member_role = discord.utils.get(interaction.guild.roles, name="Member")
            if not member_role:
                member_role = await interaction.guild.create_role(name="Member")
            
            lang_role = discord.utils.get(interaction.guild.roles, name=LANGUAGE_ROLES[lang])
            if not lang_role:
                lang_role = await interaction.guild.create_role(name=LANGUAGE_ROLES[lang])
            
            await interaction.user.add_roles(member_role, lang_role)
            
            # Store user's accepted language
            USER_LANGUAGES[interaction.user.id] = lang
            
            # Send confirmation message
            confirmation_messages = {
                "en": "You have accepted the rules and gained access to the server!",
                "tr": "Kuralları kabul ettiniz ve sunucuya erişim kazandınız!",
                "ru": "Вы приняли правила и получили доступ к серверу!",
                "ar": "لقد قبلت القواعد وحصلت على حق الوصول إلى السيرفر!",
                "az": "Qaydaları qəbul etdiniz və serverə giriş əldə etdiniz!",
                "ug": "سىز قائىدىلەرنى قوبۇل قىلدىڭىز ۋە مۇلازىمېتىرگە كىرىش ھوقۇقىغا ئېرىشتىڭىز!"
            }
            
            await interaction.response.send_message(
                confirmation_messages.get(lang, confirmation_messages["en"]),
                ephemeral=True
            )
            
            # Log the acceptance
            await log_security_event(
                interaction.guild,
                interaction.user,
                "RULES_ACCEPTED",
                f"User accepted rules in {lang} language"
            )

@bot.command(name='language', aliases=['lang', 'dil', 'язык', 'لغة', 'تىل'])
@commands.has_permissions(administrator=True)
async def change_language(ctx, lang_code: str):
    if lang_code not in LANGUAGES:
        available_langs = ", ".join([f"{code} ({name})" for code, name in LANGUAGE_NAMES.items()])
        await ctx.send(f"Available languages: {available_langs}")
        return

    server_settings[str(ctx.guild.id)] = {'language': lang_code}
    save_server_settings()
    
    # Send confirmation in the new language
    await ctx.send(LANGUAGES[lang_code].MESSAGES["language_changed"])

@bot.command(name='setup', aliases=['kur', 'установить', 'تثبيت', 'qur', 'قۇر'])
@commands.has_permissions(administrator=True)
async def manual_setup(ctx):
    await ctx.send("Starting server setup...")
    await setup_server(ctx.guild)
    await ctx.send("Server setup completed!")

@bot.command(name='purge_channels')
async def purge_channels(ctx):
    """Delete all channels in the server and optionally rebuild it (Owner only)"""
    if ctx.author.id != ctx.guild.owner_id:
        await ctx.send("Bu komutu sadece sunucu sahibi kullanabilir! | Only the server owner can use this command!")
        return

    await ctx.send("❌ Kanallar silinemedi! Bunun yerine !purge_all komutunu kullanın. | Channels could not be deleted! Use !purge_all command instead.")

@bot.command(name='purge_all')
async def purge_all(ctx):
    """Delete everything in the server except the server itself (Owner only)"""
    if ctx.author.id != ctx.guild.owner_id:
        await ctx.send("Bu komutu sadece sunucu sahibi kullanabilir! | Only the server owner can use this command!")
        return

    # Create a temporary channel to send status updates
    temp_channel = await ctx.guild.create_text_channel('deleting-everything')
    await temp_channel.send("Sunucudaki her şey siliniyor... | Deleting everything in the server...")

    # Log the action
    await log_security_event(
        ctx.guild,
        ctx.author,
        "SERVER_PURGE",
        "Server owner initiated complete server purge"
    )

    try:
        # Delete all roles except @everyone
        await temp_channel.send("Roller siliniyor... | Deleting roles...")
        roles_to_delete = [role for role in ctx.guild.roles if role.name != "@everyone"]
        for role in roles_to_delete:
            try:
                await role.delete()
            except:
                continue

        # Delete all emojis
        await temp_channel.send("Emojiler siliniyor... | Deleting emojis...")
        for emoji in ctx.guild.emojis:
            try:
                await emoji.delete()
            except:
                continue

        # Delete all channels and categories
        await temp_channel.send("Kanallar ve kategoriler siliniyor... | Deleting channels and categories...")
        
        # First, delete all channels that are not in categories
        for channel in ctx.guild.channels:
            if not channel.category and channel.id != temp_channel.id:
                try:
                    await channel.delete()
                except:
                    continue

        # Then delete all channels in categories
        for category in ctx.guild.categories:
            for channel in category.channels:
                if channel.id != temp_channel.id:
                    try:
                        await channel.delete()
                    except:
                        continue
            # Delete the category itself
            try:
                await category.delete()
            except:
                continue

        # Final cleanup - delete any remaining channels
        for channel in ctx.guild.channels:
            if channel.id != temp_channel.id:
                try:
                    await channel.delete()
                except:
                    continue

        # Final message
        await temp_channel.send("✅ Sunucudaki her şey başarıyla silindi! Sunucuyu yeniden kurmak için !setup yazın. | Everything in the server has been successfully deleted! Type !setup to rebuild the server.")
        
        # Delete the temporary channel after 10 seconds
        await asyncio.sleep(10)
        await temp_channel.delete()

    except Exception as e:
        await temp_channel.send(f"❌ Hata oluştu: {str(e)} | An error occurred: {str(e)}")

def is_command(message, cmd_type):
    """Check if the message content matches any command alias in any language"""
    content = message.content.lower()
    for lang in LANGUAGES.values():
        if content in lang.COMMANDS.get(cmd_type, []):
            return True
    return False

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    # Process commands in all languages
    await bot.process_commands(message)

    # Get server language
    lang = get_server_language(message.guild.id) if message.guild else 'en'
    lang_module = LANGUAGES[lang]

    # Handle help command in any language
    if is_command(message, "help"):
        help_text = f"""
Available commands:
• !language [en/tr/ru/ar/az/ug] - Change server language
• !help - Show this help message
• !role - Manage roles
• !giverole [role_name] [language_code] - Get a one-time role in your preferred language
• !myroles - View your role status

Personal Notes (Use in DM only):
• !id - Get your personal ID
• !note [content] - Add a new personal note
• !notes - View all your notes
• !clear_notes - Delete all your notes
"""
        await message.channel.send(help_text)

    # Check for profanity
    content_lower = message.content.lower()
    is_profanity = False
    
    # Check in all languages
    for lang_patterns in PROFANITY_PATTERNS.values():
        if any(word in content_lower for word in lang_patterns):
            is_profanity = True
            break
    
    if is_profanity:
        # Delete message
        await message.delete()
        
        # Ban user
        try:
            reason = "Automatic ban: Profanity detected"
            await message.author.ban(reason=reason, delete_message_days=7)
            
            # Log the event
            await log_security_event(
                message.guild,
                message.author,
                "PROFANITY_BAN",
                f"User banned for profanity. Message content: {message.content}"
            )
            
            # Create detailed log
            log_data = {
                "user_info": {
                    "id": message.author.id,
                    "name": str(message.author),
                    "created_at": str(message.author.created_at),
                    "joined_at": str(message.author.joined_at),
                    "roles": [role.name for role in message.author.roles]
                },
                "message_info": {
                    "content": message.content,
                    "timestamp": str(message.created_at),
                    "channel": str(message.channel)
                },
                "ban_info": {
                    "reason": reason,
                    "timestamp": datetime.datetime.now().isoformat()
                }
            }
            
            # Save to detailed log file
            with open(f'logs/ban_{message.author.id}.json', 'w', encoding='utf-8') as f:
                json.dump(log_data, f, indent=4, ensure_ascii=False)
                
        except discord.Forbidden:
            await message.channel.send("Error: Bot doesn't have permission to ban users.")

    # Check for academic discussions in wrong channels
    academic_keywords = {
        # English keywords
        "en": [
            "religion", "islam", "christianity", "judaism", "buddhism", "hinduism",
            "history", "historical", "ancient", "medieval", "modern era",
            "philosophy", "philosophical", "ethics", "metaphysics", "epistemology"
        ],
        # Turkish keywords
        "tr": [
            "din", "islam", "hristiyan", "yahudi", "budizm", "hinduizm",
            "tarih", "tarihi", "antik", "ortaçağ", "modern dönem",
            "felsefe", "felsefi", "etik", "metafizik", "epistemoloji",
            "inanç", "mezhep", "tasavvuf", "kelam", "akaid"
        ],
        # Russian keywords
        "ru": [
            "религия", "ислам", "христианство", "иудаизм", "буддизм", "индуизм",
            "история", "исторический", "древний", "средневековый", "современный",
            "философия", "философский", "этика", "метафизика", "эпистемология",
            "вера", "конфессия", "теология", "догматика"
        ],
        # Arabic keywords
        "ar": [
            "دين", "إسلام", "مسيحية", "يهودية", "بوذية", "هندوسية",
            "تاريخ", "تاريخي", "قديم", "العصور الوسطى", "العصر الحديث",
            "فلسفة", "فلسفي", "أخلاق", "ميتافيزيقيا", "نظرية المعرفة",
            "عقيدة", "مذهب", "تصوف", "علم الكلام", "عقائد"
        ],
        # Azerbaijani keywords
        "az": [
            "din", "islam", "xristianlıq", "yəhudilik", "buddizm", "hinduizm",
            "tarix", "tarixi", "qədim", "orta əsr", "müasir dövr",
            "fəlsəfə", "fəlsəfi", "etika", "metafizika", "epistemologiya",
            "inanc", "məzhəb", "təsəvvüf", "kəlam", "əqidə"
        ],
        # Uyghur keywords
        "ug": [
            "دىن", "ئىسلام", "خرىستىيان", "يەھۇدى", "بۇددا", "ھىندى",
            "تارىخ", "تارىخىي", "قەدىمكى", "ئوتتۇرا ئەسىر", "زامانىۋى دەۋر",
            "پەلسەپە", "پەلسەپىۋى", "ئەخلاق", "مېتافىزىكا", "ئېپىستېمولوگىيە",
            "ئېتىقاد", "مەزھەپ", "تەسەۋۋۇپ", "كالام", "ئەقىدە"
        ]
    }
    
    if message.channel.name not in ["🕌-religion-studies", "📜-history-studies", "🎭-philosophy-studies"]:
        # Check message content against keywords in all languages
        message_lower = message.content.lower()
        found_academic_discussion = False
        
        for lang_keywords in academic_keywords.values():
            if any(keyword in message_lower for keyword in lang_keywords):
                found_academic_discussion = True
                break
        
        if found_academic_discussion:
            # Delete message
            await message.delete()
            
            # Warn user
            WARN_COUNTS[message.author.id] += 1
            warn_count = WARN_COUNTS[message.author.id]
            
            if warn_count == 1:
                warning_messages = {
                    "en": f"{message.author.mention}, first warning: Academic discussions must be in appropriate channels. Please use 🕌-religion-studies, 📜-history-studies, or 🎭-philosophy-studies channels.",
                    "tr": f"{message.author.mention}, ilk uyarı: Akademik tartışmalar uygun kanallarda yapılmalıdır. Lütfen 🕌-religion-studies, 📜-history-studies veya 🎭-philosophy-studies kanallarını kullanın.",
                    "ru": f"{message.author.mention}, первое предупреждение: Академические дискуссии должны вестись в соответствующих каналах. Пожалуйста, используйте каналы 🕌-religion-studies, 📜-history-studies или 🎭-philosophy-studies.",
                    "ar": f"{message.author.mention}, التحذير الأول: يجب أن تكون المناقشات الأكاديمية في القنوات المناسبة. يرجى استخدام قنوات 🕌-religion-studies أو 📜-history-studies أو 🎭-philosophy-studies.",
                    "az": f"{message.author.mention}, xəbərdarlıq {warn_count}/2: Akademik müzakirələr müvafiq kanallarda aparılmalıdır. Zəhmət olmasa 🕌-religion-studies, 📜-history-studies və ya 🎭-philosophy-studies kanallarından istifadə edin.",
                    "ug": f"{message.author.mention}, ئاگاھلاندۇرۇش {warn_count}/2: ئاكادېمىك مۇنازىرىلەرگە قاتنىشىش ئۈچۈن دەلىللىنىشىڭىزگە سەۋەب بولىدۇ."
                }
                
                # Send warning in server language
                server_lang = get_server_language(message.guild.id)
                await message.channel.send(warning_messages.get(server_lang, warning_messages["en"]), delete_after=10)
            
            elif warn_count == 2:
                final_warning_messages = {
                    "en": f"{message.author.mention}, final warning: Next violation will result in a ban.",
                    "tr": f"{message.author.mention}, son uyarı: Bir sonraki ihlal banlanmanıza neden olacak.",
                    "ru": f"{message.author.mention}, последнее предупреждение: Следующее нарушение приведет к бану.",
                    "ar": f"{message.author.mention}, التحذير النهائي: المخالفة التالية ستؤدي إلى الحظر.",
                    "az": f"{message.author.mention}, son xəbərdarlıq: Növbəti pozuntu qadağaya səbəb olacaq.",
                    "ug": f"{message.author.mention}, ئاخىرقى ئاگاھلاندۇرۇش: كېيىنكى خىلاپلىق چەكلىنىشىڭىزگە سەۋەب بولىدۇ."
                }
                
                server_lang = get_server_language(message.guild.id)
                await message.channel.send(final_warning_messages.get(server_lang, final_warning_messages["en"]), delete_after=10)
            
            else:
                # Ban user after third warning
                reason = "Repeated unauthorized academic discussions"
                await message.author.ban(reason=reason)
                
                # Log the ban
                await log_security_event(
                    message.guild,
                    message.author,
                    "ACADEMIC_DISCUSSION_BAN",
                    f"User banned for repeated unauthorized academic discussions. Warning count: {warn_count}"
                )
                
                # Create detailed ban log
                log_data = {
                    "user_info": {
                        "id": message.author.id,
                        "name": str(message.author),
                        "warning_count": warn_count
                    },
                    "ban_info": {
                        "reason": reason,
                        "timestamp": datetime.datetime.now().isoformat()
                    }
                }
                
                with open(f'logs/academic_ban_{message.author.id}.json', 'w', encoding='utf-8') as f:
                    json.dump(log_data, f, indent=4, ensure_ascii=False)

    await bot.process_commands(message)

# Create logs directory if it doesn't exist
os.makedirs('logs', exist_ok=True)

# Channel protection
@bot.event
async def on_guild_channel_delete(channel):
    async for entry in channel.guild.audit_logs(action=discord.AuditLogAction.channel_delete, limit=1):
        if entry.user.id != channel.guild.owner_id:  # If not the server owner
            # Restore the channel
            if isinstance(channel, discord.TextChannel):
                restored_channel = await channel.clone(name=channel.name)
                await restored_channel.edit(position=channel.position)
                
                # Log the event
                await log_security_event(
                    channel.guild,
                    entry.user,
                    "UNAUTHORIZED_CHANNEL_DELETE",
                    f"User attempted to delete channel {channel.name}. Channel has been restored."
                )
                
                # Remove admin permissions if they have it
                admin_role = discord.utils.get(channel.guild.roles, name="🛡️ Admin")
                if admin_role in entry.user.roles:
                    await entry.user.remove_roles(admin_role)
                    await log_security_event(
                        channel.guild,
                        entry.user,
                        "ADMIN_PERMISSION_REVOKED",
                        "Admin permissions revoked due to unauthorized channel deletion attempt"
                    )

# Role protection
@bot.event
async def on_guild_role_delete(role):
    async for entry in role.guild.audit_logs(action=discord.AuditLogAction.role_delete, limit=1):
        if entry.user.id != role.guild.owner_id:  # If not the server owner
            # Restore the role
            restored_role = await role.guild.create_role(
                name=role.name,
                permissions=role.permissions,
                color=role.color,
                hoist=role.hoist,
                mentionable=role.mentionable
            )
            
            # Log the event
            await log_security_event(
                role.guild,
                entry.user,
                "UNAUTHORIZED_ROLE_DELETE",
                f"User attempted to delete role {role.name}. Role has been restored."
            )
            
            # Remove admin permissions if they have it
            admin_role = discord.utils.get(role.guild.roles, name="🛡️ Admin")
            if admin_role in entry.user.roles:
                await entry.user.remove_roles(admin_role)
                await log_security_event(
                    role.guild,
                    entry.user,
                    "ADMIN_PERMISSION_REVOKED",
                    "Admin permissions revoked due to unauthorized role deletion attempt"
                )

# Add new commands
@bot.command(name='id')
async def show_id(ctx):
    embed = discord.Embed(
        title="Your Personal ID",
        description=f"Your unique ID is: {ctx.author.id}",
        color=discord.Color.blue()
    )
    embed.add_field(name="Usage", value="Use this ID with the note commands to manage your personal notes.")
    await ctx.author.send(embed=embed)
    if ctx.guild:
        await ctx.message.delete()
        temp = await ctx.send("I've sent your ID in a private message!")
        await asyncio.sleep(5)
        await temp.delete()

@bot.command(name='note')
async def add_note(ctx, *, content: str):
    """Add a personal note"""
    if not isinstance(ctx.channel, discord.DMChannel):
        await ctx.message.delete()
        temp = await ctx.send("Please use this command in DM to protect your privacy!")
        await asyncio.sleep(5)
        await temp.delete()
        return

    await save_note(ctx.author.id, content)
    embed = discord.Embed(
        title="Note Saved",
        description="Your note has been securely saved!",
        color=discord.Color.green()
    )
    await ctx.send(embed=embed)

@bot.command(name='notes')
async def view_notes(ctx):
    """View all your personal notes"""
    if not isinstance(ctx.channel, discord.DMChannel):
        await ctx.message.delete()
        temp = await ctx.send("Please use this command in DM to protect your privacy!")
        await asyncio.sleep(5)
        await temp.delete()
        return

    notes = await get_notes(ctx.author.id)
    if not notes:
        await ctx.send("You don't have any notes yet!")
        return

    embed = discord.Embed(
        title="Your Personal Notes",
        color=discord.Color.blue()
    )
    
    for i, note in enumerate(notes, 1):
        if len(note) > 1024:  # Discord embed field value limit
            note = note[:1021] + "..."
        embed.add_field(name=f"Note {i}", value=note, inline=False)

    await ctx.send(embed=embed)

@bot.command(name='clear_notes')
async def clear_notes(ctx):
    """Clear all your personal notes"""
    if not isinstance(ctx.channel, discord.DMChannel):
        await ctx.message.delete()
        temp = await ctx.send("Please use this command in DM to protect your privacy!")
        await asyncio.sleep(5)
        await temp.delete()
        return

    try:
        os.remove(f'{NOTES_DIR}/{ctx.author.id}_notes.enc')
        embed = discord.Embed(
            title="Notes Cleared",
            description="All your notes have been deleted!",
            color=discord.Color.green()
        )
    except FileNotFoundError:
        embed = discord.Embed(
            title="No Notes Found",
            description="You don't have any notes to clear!",
            color=discord.Color.red()
        )
    
    await ctx.send(embed=embed)

@bot.command(name='giverole')
async def give_role(ctx, role_name: str, lang_code: str = None):
    """Give a one-time role to a user in their preferred language"""
    # Check if role exists in translations
    if role_name.lower() not in ROLE_TRANSLATIONS:
        available_roles = ", ".join(ROLE_TRANSLATIONS.keys())
        await ctx.send(f"Available roles: {available_roles}")
        return

    # Check if role was already assigned to this user
    if ctx.author.id in ASSIGNED_ROLES[role_name.lower()]:
        await ctx.send("You have already received this role!")
        return

    # If language not specified, use server default
    if not lang_code:
        lang_code = get_server_language(ctx.guild.id)
    
    # Validate language code
    if lang_code not in LANGUAGES:
        available_langs = ", ".join(LANGUAGE_NAMES.keys())
        await ctx.send(f"Available languages: {available_langs}")
        return

    # Get role name in requested language
    role_name_translated = ROLE_TRANSLATIONS[role_name.lower()][lang_code]

    # Check if role exists, create if not
    role = discord.utils.get(ctx.guild.roles, name=role_name_translated)
    if not role:
        role = await ctx.guild.create_role(
            name=role_name_translated,
            color=discord.Color.gold(),
            hoist=True,  # Show role separately in member list
            mentionable=True
        )

    # Assign role and track assignment
    try:
        await ctx.author.add_roles(role)
        ASSIGNED_ROLES[role_name.lower()].add(ctx.author.id)
        
        embed = discord.Embed(
            title="Role Assigned!",
            description=f"You have been given the role: {role_name_translated}",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)
        
        # Log the role assignment
        await log_security_event(
            ctx.guild,
            ctx.author,
            "ROLE_ASSIGNED",
            f"User received one-time role: {role_name_translated}"
        )
    except discord.Forbidden:
        await ctx.send("Error: Bot doesn't have permission to assign roles.")

@bot.command(name='myroles')
async def my_roles(ctx):
    """Show all available roles and which ones you have received"""
    embed = discord.Embed(
        title="Your Role Status",
        color=discord.Color.blue()
    )
    
    for role_name in ROLE_TRANSLATIONS:
        status = "✅ Received" if ctx.author.id in ASSIGNED_ROLES[role_name] else "❌ Not Received"
        embed.add_field(
            name=role_name.upper(),
            value=status,
            inline=False
        )
    
    await ctx.send(embed=embed)

@bot.command(name='setlanguage')
async def set_language(ctx, lang_code: str):
    """Set your preferred language and get the corresponding role"""
    if lang_code not in LANGUAGES:
        available_langs = ", ".join([f"{code} ({name})" for code, name in LANGUAGE_NAMES.items()])
        await ctx.send(f"Available languages: {available_langs}")
        return

    # Remove existing language roles
    for role in ctx.author.roles:
        if role.name in LANGUAGE_ROLES.values():
            await ctx.author.remove_roles(role)

    # Get or create new language role
    role_name = LANGUAGE_ROLES[lang_code]
    role = discord.utils.get(ctx.guild.roles, name=role_name)
    if not role:
        role = await ctx.guild.create_role(
            name=role_name,
            color=discord.Color.blue(),
            hoist=True,
            mentionable=True
        )

    # Assign new language role
    await ctx.author.add_roles(role)
    
    # Store user's language preference
    USER_LANGUAGES[ctx.author.id] = lang_code
    
    # Send confirmation in user's new language
    confirmation_messages = {
        "en": "Your language has been set to English!",
        "tr": "Diliniz Türkçe olarak ayarlandı!",
        "ru": "Ваш язык установлен на русский!",
        "ar": "تم تعيين لغتك إلى العربية!",
        "az": "Diliniz Azərbaycan dilinə təyin edildi!",
        "ug": "تىلىڭىز ئۇيغۇرچىغا تەڭشەلدى!"
    }
    
    await ctx.send(confirmation_messages[lang_code])

# Add user language tracking
USER_LANGUAGES = {}  # user_id -> language_code

# Update warning system to use user's language
async def send_warning(message, warning_type, warn_count):
    user_lang = USER_LANGUAGES.get(message.author.id, get_server_language(message.guild.id))
    
    if warning_type == "academic":
        warning_messages = {
            "en": f"{message.author.mention}, warning {warn_count}/2: Academic discussions must be in appropriate channels. Please use 🕌-religion-studies, 📜-history-studies, or 🎭-philosophy-studies channels.",
            "tr": f"{message.author.mention}, uyarı {warn_count}/2: Akademik tartışmalar uygun kanallarda yapılmalıdır. Lütfen 🕌-religion-studies, 📜-history-studies veya 🎭-philosophy-studies kanallarını kullanın.",
            "ru": f"{message.author.mention}, предупреждение {warn_count}/2: Академические дискуссии должны вестись в соответствующих каналах. Пожалуйста, используйте каналы 🕌-religion-studies, 📜-history-studies или 🎭-philosophy-studies.",
            "ar": f"{message.author.mention}, تحذير {warn_count}/2: يجب أن تكون المناقشات الأكاديمية في القنوات المناسبة. يرجى استخدام قنوات 🕌-religion-studies أو 📜-history-studies أو 🎭-philosophy-studies.",
            "az": f"{message.author.mention}, xəbərdarlıq {warn_count}/2: Akademik müzakirələr müvafiq kanallarda aparılmalıdır. Zəhmət olmasa 🕌-religion-studies, 📜-history-studies və ya 🎭-philosophy-studies kanallarından istifadə edin.",
            "ug": f"{message.author.mention}, ئاگاھلاندۇرۇش {warn_count}/2: ئاكادېمىك مۇنازىرىلەرگە قاتنىشىش ئۈچۈن دەلىللىنىشىڭىزگە سەۋەب بولىدۇ."
        }
        
        if warn_count == 2:
            final_warning_messages = {
                "en": f"{message.author.mention}, final warning: Next violation will result in a ban.",
                "tr": f"{message.author.mention}, son uyarı: Bir sonraki ihlal banlanmanıza neden olacak.",
                "ru": f"{message.author.mention}, последнее предупреждение: Следующее нарушение приведет к бану.",
                "ar": f"{message.author.mention}, التحذير النهائي: المخالفة التالية ستؤدي إلى الحظر.",
                "az": f"{message.author.mention}, son xəbərdarlıq: Növbəti pozuntu qadağaya səbəb olacaq.",
                "ug": f"{message.author.mention}, ئاخىرقى ئاگاھلاندۇرۇش: كېيىنكى خىلاپلىق چەكلىنىشىڭىزگە سەۋەب بولىدۇ."
            }
            await message.channel.send(final_warning_messages.get(user_lang, final_warning_messages["en"]), delete_after=10)
        else:
            await message.channel.send(warning_messages.get(user_lang, warning_messages["en"]), delete_after=10)

# Run the bot with token
bot.run(TOKEN) 