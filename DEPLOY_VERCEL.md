# 🚀 دليل رفع وتشغيل منصة AutoCorp على Vercel بالكامل

تم تصميم منصة **AutoCorp** لتعمل بشكل مثالي كـ **Serverless Application** على منصة **Vercel** دون أي مكتبات ثنائية معقدة، بالاعتماد على:
1. **Vercel Serverless Functions (`@vercel/python`)** لتشغيل واجهات FastAPI.
2. **Turso libSQL Cloud (`/v2/pipeline`)** عبر اتصالات HTTPS مشفرة تضمن استقرار وسرعة قواعد البيانات دون الحاجة لملفات SQLite محلية.
3. **Telegram Webhook** لاستقبال رسائل تيليجرام ومعالجتها لحظياً.

---

## 📋 الخطوة 1: الرفع عبر Vercel Dashboard (طريقة الـ 1-Click)

1. ادخل إلى حسابك على [Vercel.com](https://vercel.com).
2. اضغط على زر **"Add New..."** ثم اختر **"Project"**.
3. قم بربط مستودع GitHub الخاص بك:
   ```
   https://github.com/alfarouq637/-Agents-at-Work-Project.git
   ```
4. في شاشة إعدادات المشروع (Configure Project):
   - **Framework Preset**: اتركه **Other** (يتعرف Vercel تلقائياً على `vercel.json`).
   - **Root Directory**: `./` (المجلد الرئيسي).
   - **Build Command**: اتركه فارغاً.
   - **Output Directory**: اتركه فارغاً.

---

## 🔑 الخطوة 2: ضبط متغيرات البيئة (Environment Variables) في Vercel

قبل الضغط على **Deploy**، افتح قسم **Environment Variables** في Vercel وأضف المتغيرات التالية:

| اسم المتغير (Variable Name) | القيمة المقترحة (Value) | الوصف |
| :--- | :--- | :--- |
| `VERCEL` | `1` | تفعيل وضع السيرفرلس |
| `TURSO_DATABASE_URL` | `libsql://your-db.aws-eu-west-1.turso.io` | رابط قاعدة بيانات Turso Cloud |
| `TURSO_AUTH_TOKEN` | `eyJhbGciOi...` | توكن المصادقة المشفر لقاعدة Turso |
| `ADMIN_PASSWORD` | `AlfarouqIbrahim` (أو كلمة سرك) | كلمة مرور المشرف العام لحماية لوحة الإدارة |
| `ADMIN_KEY` | `autocorp-admin-secret-2026` | مفتاح التوكن السري للمشرف |
| `AUTH_SECRET_KEY` | `autocorp-jwt-salt-secure-2026` | مفتاح تشفير توكنات تسجيل دخول العملاء |
| `TELEGRAM_BOT_TOKEN` | `8620532191:AAGha00LT89LYPtZxelOyiKgrxw8p3KaGdA` | توكن بوت التيليجرام الرسمي |
| `TELEGRAM_BOT_USERNAME` | `autocorp_Alfarouq_Ibrahim_bot` | يوزر نيم البوت |
| `OPENROUTER_API_KEY` | مفتاح OpenRouter الخاص بك | اختياري لتوليد النصوص والنماذج الذكية |
| `NVIDIA_API_KEY` | مفتاح NVIDIA NIM الخاص بك | اختياري لنموذج الرؤية وتحليل صور المنيو |
| `GROQ_API_KEY` | مفتاح Groq الخاص بك | اختياري للمحادثة السريعة |
| `MOCK` | `0` (أو `1` للمحاكاة بدون رصيد) | وضع التشغيل |

---

## 🌐 الخطوة 3: تفعيل Webhook لبوت تيليجرام على Vercel

بعد إتمام الرفع والحصول على رابط موقعك على Vercel (مثال: `https://autocorp.vercel.app`):
قم بتفعيل الـ Webhook حتى يستقبل بوت التيليجرام الرسائل عبر السيرفرلس:

افتح المتصفح أو موجه الأوامر واطلب الرابط التالي:
```bash
curl "https://api.telegram.org/bot8620532191:AAGha00LT89LYPtZxelOyiKgrxw8p3KaGdA/setWebhook?url=https://YOUR_VERCEL_DOMAIN.vercel.app/telegram"
```
*(استبدل `YOUR_VERCEL_DOMAIN` برابط مشروعك الذي يمنحه لك Vercel).*

---

## ✅ التحقق بعد الرفع:
- **الرئيسية واللاندينج بيدج**: `https://YOUR_VERCEL_DOMAIN.vercel.app/`
- **لوحة المشرف العام**: اضغط على "👑 لوحة المشرف" وأدخل كلمة المرور.
- **تطبيق العميل**: `https://YOUR_VERCEL_DOMAIN.vercel.app/sites/5/`
- **بوت التيليجرام**: أرسل رسالة للبوت على `@autocorp_Alfarouq_Ibrahim_bot` وسيرد عليك فوراً.
