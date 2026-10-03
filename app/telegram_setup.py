"""AutoCorp Telegram Bot Profile & Command Configurator.
Configures the bot description, short description, and commands via Telegram API.
"""
import os
from pathlib import Path
from dotenv import load_dotenv
import httpx

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()

DESCRIPTION = """⚡ AutoCorp — وكالة الذكاء الاصطناعي ذاتية التشغيل للشركات والمتاجر المصرية الناشئة.

🚀 ماذا يمكن للبوت أن يفعل لأجلك؟
• ابنِ موقعك الإلكتروني ومتجرك الكامل في دقيقتين فقط.
• أرسل صورة المنيو أو المنتجات وسيقوم محلل الرؤية (Vision Analyst) ببرمجة المتجر وتجهيز السلة وبوابات الدفع تلقائياً.
• بوابات دفع مصرية مدمجة: فودافون كاش، إنستاباي، فوري، وكاش عند الاستلام.
• ربط دومين مخصص وتصدير حزم استضافة هوستينجر (Hostinger).

👨‍💼 للدخول كمدير مشرف للموافقة على القرارات: أرسل الأمر /admin متبوعاً بكلمة المرور.
"""

SHORT_DESCRIPTION = "⚡ وكالة الذكاء الاصطناعي المتكاملة لبناء مواقع ومتاجر الشركات المصرية الناشئة في دقيقتين."

COMMANDS = [
    {"command": "start", "description": "بدء استخدام الوكالة وطلب موقع جديد"},
    {"command": "admin", "description": "دخول المشرف العام للموافقات وإدارة الوكالة"},
    {"command": "help", "description": "شرح الخدمات وطريقة إنشاء المتاجر وبوابات الدفع"}
]

def setup_bot():
    if not BOT_TOKEN:
        print("⚠️ TELEGRAM_BOT_TOKEN is not set in .env")
        return False
        
    base_url = f"https://api.telegram.org/bot{BOT_TOKEN}"
    
    with httpx.Client(timeout=15.0) as client:
        # 1. setMyDescription
        try:
            r = client.post(f"{base_url}/setMyDescription", json={"description": DESCRIPTION})
            print("setMyDescription:", r.status_code, r.json().get("ok"))
        except Exception as e:
            print("setMyDescription error:", e)
            
        # 2. setMyShortDescription
        try:
            r = client.post(f"{base_url}/setMyShortDescription", json={"short_description": SHORT_DESCRIPTION})
            print("setMyShortDescription:", r.status_code, r.json().get("ok"))
        except Exception as e:
            print("setMyShortDescription error:", e)
            
        # 3. setMyCommands
        try:
            r = client.post(f"{base_url}/setMyCommands", json={"commands": COMMANDS})
            print("setMyCommands:", r.status_code, r.json().get("ok"))
        except Exception as e:
            print("setMyCommands error:", e)

    print("\n✅ Bot descriptions and commands updated on Telegram!")
    print("ℹ️ Note for Bot Profile Picture (Avatar):")
    print("Telegram does not allow setting a bot's avatar via API. To set the profile picture:")
    print("1. Open @BotFather on Telegram.")
    print("2. Type: /setuserpic")
    print("3. Select your bot.")
    print("4. Send the image file: bot_avatar.jpg (already generated in your project root).")
    return True

if __name__ == "__main__":
    setup_bot()
