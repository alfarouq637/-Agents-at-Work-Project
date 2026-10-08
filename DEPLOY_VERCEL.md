# نشر AutoCorp على Vercel — دليل آمن لبيئة المعاينة

> هذا الدليل يجهز نسخة معاينة محمية من التطبيق الحالي، وليس إقراراً بأن
> المنصة جاهزة للإنتاج أو متاحة دائماً. لا تنشر بيانات عملاء أو تدفق دفع حي
> قبل استيفاء بوابات الإصدار في
> [خطة المعالجة](docs/ENTERPRISE_REMEDIATION_PLAN.md).

## قبل النشر

1. دوّر كل سر استُخدم تاريخياً، ثم خزّنه في مدير أسرار Vercel فقط.
2. شغّل محلياً `python -m pip install -r requirements.txt` ثم `pytest -q`.
3. استخدم قاعدة Turso منفصلة للمعاينة؛ لا تعتمد على SQLite المحلي، لأن قرص
   Vercel مؤقت ولا يصلح كقاعدة بيانات مشتركة.
4. لا تضع أسرار الإنتاج في Preview deployments أو في ملفات `.env` المتتبعة.

## إعداد المشروع

- اربط المستودع من Vercel واختر **Other** وRoot Directory: `./`.
- لا تضف المتغير `VERCEL` يدوياً؛ تضبطه منصة Vercel وقت التشغيل.
- لا تضف Build Command مخصصاً. نقطة الدخول هي `api/index.py` وتعرّض تطبيق
  FastAPI باسم `app`، وهو النمط المدعوم في
  [Python Runtime](https://vercel.com/docs/functions/runtimes/python).
- لا تفعّل أياً من متغيرات `ENABLE_*` عالية الخطورة.

## متغيرات بيئة الإنتاج المطلوبة

أضف القيم في **Project Settings → Environment Variables**، واختر Production
فقط للأسرار. التغييرات لا تسري على نشر قائم حتى تعيد النشر.

| المتغير | الغرض |
| --- | --- |
| `TURSO_DATABASE_URL` | عنوان قاعدة Turso الإنتاجية المنفصلة. |
| `TURSO_AUTH_TOKEN` | رمز Turso محدود الصلاحية. |
| `AUTH_SECRET_KEY` | قيمة عشوائية عالية الإنتروبيا لتوقيع الجلسات. |
| `ADMIN_PASSWORD` | كلمة مرور مشرف فريدة وطويلة؛ لا تستخدمها في Telegram. |
| `PUBLIC_URL` | رابط HTTPS الأساسي فقط، مثل `https://app.example.com`. |
| `TRUSTED_ORIGINS` | أصول الويب الأولى الإضافية مفصولة بفواصل؛ اتركه فارغاً إن لم توجد. |
| `MAINTENANCE_MODE` | اتركه `0` عادةً؛ اضبطه مؤقتاً على `1` أثناء الاستجابة للحوادث أو تدوير الأسرار لمنع كل عمليات الكتابة. |
| `TELEGRAM_BOT_TOKEN` | اختياري؛ رمز البوت بعد تدويره. |
| `TELEGRAM_SECRET` | مطلوب عند تفعيل webhook؛ قيمة عشوائية مستقلة. |
| `TELEGRAM_OWNER_CHAT_ID` | اختياري؛ Chat ID الوحيد الذي يستطيع اعتماد العمليات. |

عند وجود `PUBLIC_URL` يبدأ بـ`https://` يفعّل التطبيق تلقائياً HSTS ووسم
`Secure` لملف الجلسة. اترك كل مفاتيح `ENABLE_DIRECT_DEPLOYMENT` و
`ENABLE_TENANT_FILE_EDITOR` و`ENABLE_TENANT_SQL_CONSOLE` و
`ENABLE_TENANT_BOT_CREDENTIALS` و`ENABLE_DEMO_PAYMENT_ACTIVATION` على `0`.

عند تمكين `MAINTENANCE_MODE=1` تظل الصفحات و`GET /api/healthz` متاحة للقراءة،
لكن التطبيق يرفض كل `POST` و`PUT` و`PATCH` و`DELETE` (بما فيها Telegram
والـwebhooks) بـ`503`. أعده إلى `0` فقط بعد اكتمال التدوير والتحقق من النشر.

توضح وثائق Vercel أن الأسرار متاحة لكل نشر جديد في البيئة المحددة، لذا أعد
النشر بعد الإضافة أو التدوير ولا تضعها في الشيفرة أو سجلات البناء. راجع
[إدارة متغيرات Vercel](https://vercel.com/docs/environment-variables).

## Telegram webhook (اختياري)

فعّل البوت فقط بعد أن تصبح `https://YOUR_DOMAIN/api/healthz` جاهزة وتضبط
`PUBLIC_URL` على نفس الأصل. يرفض التطبيق webhook بلا رأس
`X-Telegram-Bot-Api-Secret-Token`.

احفظ `TELEGRAM_BOT_TOKEN` و`TELEGRAM_SECRET` كمتغيرات بيئة في جلسة طرفية
خاصة (لا تضع القيم حرفياً في history أو دردشة)، ثم نفّذ:

```bash
curl --fail --silent --show-error \
  -F "url=${PUBLIC_URL%/}/telegram" \
  -F "secret_token=${TELEGRAM_SECRET}" \
  "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/setWebhook"
```

يعتمد ذلك على `secret_token` الرسمي لـ`setWebhook`؛ تؤكد وثائق Telegram أن
webhook يجب أن يكون HTTPS وأنه يمكن تعيينه عبر هذه العملية. راجع
[دليل Telegram Webhooks](https://core.telegram.org/bots/webhooks).

## بوابة التحقق بعد النشر

1. تحقق من `GET /api/healthz`. يجب أن يعود `200` مع `ready: true` و
   `database_ready: true` ومن دون إعدادات أو تبعيات مطلوبة مفقودة.
2. تحقق من تسجيل مستخدم تجريبي ثم تسجيل خروجه؛ يجب أن يكون ملف الجلسة
   `HttpOnly` و`Secure`، وأن تصبح النسخة المنسوخة من الجلسة غير صالحة بعد
   الخروج.
3. اختبر Telegram برسالة غير حساسة فقط، ثم راجع أن `TELEGRAM_SECRET` غير
   موجود في الاستجابات أو السجلات.
4. لا تفعّل الدفع أو النشر المباشر أو بيانات بوت التاجر من هذه النسخة.

## قيود الاستضافة الحالية

Vercel مناسب لهذه الواجهة والمعاينات القصيرة وwebhook، لكنه ليس منصة للمهام
الدائمة أو polling أو سير عمل الوكلاء طويل الأمد. يستمر polling محلياً فقط؛
الإنتاج يحتاج webhook وعمّال/طابوراً دائماً قبل الادعاء بالتشغيل المستمر.
يتطلب الهدف النهائي PostgreSQL مع RLS وتخزين كائنات وoutbox ومراقبة ونسخاً
احتياطياً واختبارات استعادة كما هو محدد في الخطة.
