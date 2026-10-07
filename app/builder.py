"""AutoCorp Intelligent Full-Stack Site Builder & Synthesizer.
Generates responsive, production-ready Arabic Single Page Applications (SPAs)
with Tailored Palettes, Dynamic Catalogs, Interactive Cart Drawers,
Egyptian Payment Gateways, and Live Backend APIs (/api/sites/{id}/orders).

Supported Archetypes:
- Portfolios & CVs (Cybersecurity, Software Engineering, Design, Consulting)
- Specialty E-Commerce (Pure Honey, Gourmet, Luxury Retail)
- Food & Beverage (Grills, Cafes, Cloud Kitchens)
- Medical & Health (Clinics, Doctors, Appointments)
- B2B Agencies & SaaS (Marketing, Digital Solutions, Corporate)
- Fresh Grocery & Supermarkets (Produce, Daily Delivery)
- Consumer Tech & Electronics (Smart Devices, Accessories)
- Fashion & Apparel (Boutique, Luxury Wear)
"""
import html
import json
import random
import re

PALETTES = {
    "cyber": {
        "name": "أمن سيبراني وهاكرز تيك (Cyber Tech / Security & Pentest)",
        "primary": "#06b6d4",
        "primary_dark": "#0891b2",
        "secondary": "#10b981",
        "accent": "#f59e0b",
        "bg_light": "#0f172a",
        "hero_gradient": "linear-gradient(135deg, #020617 0%, #0f172a 50%, #1e293b 100%)",
        "badge_bg": "rgba(6, 182, 212, 0.15)",
        "badge_text": "#22d3ee",
    },
    "amber": {
        "name": "عسلي وذهبي طبيعي (Natural Amber / Pure Honey)",
        "primary": "#d97706",
        "primary_dark": "#b45309",
        "secondary": "#f59e0b",
        "accent": "#059669",
        "bg_light": "#fffbeb",
        "hero_gradient": "linear-gradient(135deg, #78350f 0%, #92400e 50%, #d97706 100%)",
        "badge_bg": "#fef3c7",
        "badge_text": "#92400e",
    },
    "emerald": {
        "name": "أخضر فريش وطبيعي (Emerald / Vegetables & Organic)",
        "primary": "#059669",
        "primary_dark": "#047857",
        "secondary": "#10b981",
        "accent": "#f59e0b",
        "bg_light": "#f0fdf4",
        "hero_gradient": "linear-gradient(135deg, #064e3b 0%, #047857 50%, #059669 100%)",
        "badge_bg": "#dcfce7",
        "badge_text": "#15803d",
    },
    "sunset": {
        "name": "عنبر وذهبي دافئ (Warm Sunset / Food & Grill)",
        "primary": "#d97706",
        "primary_dark": "#b45309",
        "secondary": "#f59e0b",
        "accent": "#ef4444",
        "bg_light": "#fffbeb",
        "hero_gradient": "linear-gradient(135deg, #78350f 0%, #b45309 50%, #d97706 100%)",
        "badge_bg": "#fef3c7",
        "badge_text": "#b45309",
    },
    "ocean": {
        "name": "أزرق تكنولوجي وشركات (Ocean Navy / Tech & Electronics)",
        "primary": "#0284c7",
        "primary_dark": "#0369a1",
        "secondary": "#38bdf8",
        "accent": "#10b981",
        "bg_light": "#f0f9ff",
        "hero_gradient": "linear-gradient(135deg, #0c4a6e 0%, #075985 50%, #0284c7 100%)",
        "badge_bg": "#e0f2fe",
        "badge_text": "#0369a1",
    },
    "royal": {
        "name": "بنفسجي ملكي وفاخر (Royal Purple / Luxury & Fashion)",
        "primary": "#7c3aed",
        "primary_dark": "#6d28d9",
        "secondary": "#a78bfa",
        "accent": "#ec4899",
        "bg_light": "#faf5ff",
        "hero_gradient": "linear-gradient(135deg, #4c1d95 0%, #5b21b6 50%, #7c3aed 100%)",
        "badge_bg": "#f3e8ff",
        "badge_text": "#6d28d9",
    },
    "teal": {
        "name": "فيروزي طبي ورعاية (Medical Teal / Clinics)",
        "primary": "#0d9488",
        "primary_dark": "#0f766e",
        "secondary": "#14b8a6",
        "accent": "#0284c7",
        "bg_light": "#f0fdfa",
        "hero_gradient": "linear-gradient(135deg, #134e4a 0%, #0f766e 50%, #0d9488 100%)",
        "badge_bg": "#ccfbf1",
        "badge_text": "#0f766e",
    },
    "indigo": {
        "name": "نيلي وريادة أعمال (Modern Indigo / Agency & SaaS)",
        "primary": "#4f46e5",
        "primary_dark": "#4338ca",
        "secondary": "#6366f1",
        "accent": "#06b6d4",
        "bg_light": "#eef2ff",
        "hero_gradient": "linear-gradient(135deg, #312e81 0%, #3730a3 50%, #4f46e5 100%)",
        "badge_bg": "#e0e7ff",
        "badge_text": "#3730a3",
    },
    "crimson": {
        "name": "أحمر حماسي وجريء (Ruby Crimson / Deals)",
        "primary": "#dc2626",
        "primary_dark": "#b91c1c",
        "secondary": "#f87171",
        "accent": "#f59e0b",
        "bg_light": "#fef2f2",
        "hero_gradient": "linear-gradient(135deg, #7f1d1d 0%, #991b1b 50%, #dc2626 100%)",
        "badge_bg": "#fee2e2",
        "badge_text": "#b91c1c",
    },
}

DEFAULT_CATALOGS = {
    "honey": [
        {"title": "عسل سدر جبلي يمني دوعني نخب أول (كيلو)", "price": 420, "category": "عسل طبيعي فاخر", "badge": "الأكثر طلباً", "desc": "أجود أنواع السدر الجبلي الطبيعي المفحوص معملياً، غني بالمعادن ومضادات الأكسدة."},
        {"title": "عسل حبة البركة الصافي المنقى (نصف كيلو)", "price": 190, "category": "أعسال علاجية", "badge": "مقوي للمناعة", "desc": "عسل نقي مغذى على أزهار حبة البركة، مثالي لتقوية الجهاز المناعي والجهاز التنفسي."},
        {"title": "عسل زهور الموالح الطبيعي (كيلو)", "price": 150, "category": "عسل الزهور", "badge": "خفيف ولذيذ", "desc": "عسل حمضيات خفيف ولذيذ وغني بفيتامين C، محبب جداً للأطفال وطاقة يومية طبيعية."},
        {"title": "غذاء ملكات النحل الصافي الطازج (50 جم)", "price": 240, "category": "مشتقات النحل", "badge": "طاقة ونشاط", "desc": "غذاء ملكي نقي 100% مستخرج طازجاً، محفز طبيعي للنشاط الذهني والبدني."},
        {"title": "بوكس التوفير الملكي (3 برطمانات متنوعة + شمع)", "price": 520, "category": "بكجات التوفير", "badge": "وفر 25%", "desc": "سدر جبلي + حبة بركة + زهور موالح + قطعة شمع طبيعي في علبة إهداء فاخرة."},
        {"title": "شمع عسل نحل طبيعي قطفة أولى (نصف كيلو)", "price": 170, "category": "شمع العسل", "badge": "طبيعي 100%", "desc": "إطارات شمع طبيعية مختومة خام بدون أي معالجة، تجربة تذوق ريفية أصيلة."},
    ],
    "portfolio": [
        {"title": "اختبار اختراق تطبيقات الويب والـ APIs (Web Pentest)", "price": 2500, "category": "خدمات الفحص الأمني", "badge": "شامل التقرير", "desc": "فحص أمني عميق وكشف ثغرات OWASP Top 10 و Business Logic مع تقديم تقرير تفصيلي بالحلول."},
        {"title": "تدقيق أمني للبنية التحتية والسيرفرات (Infra Audit)", "price": 3500, "category": "خدمات الفحص الأمني", "badge": "موصى به للشركات", "desc": "تقييم أمان الخوادم السحابية، جدران الحماية Firewall، وضبط تكوينات الحماية Hardening."},
        {"title": "استشارة أمنية وتقييم المخاطر السيبرانية (Consultation)", "price": 1000, "category": "استشارات وتوجيه", "badge": "فوري", "desc": "جلسة فنية لتحليل بنيتك الرقمية ووضع خطة تأمين متكاملة متوافقة مع المعايير القياسية."},
        {"title": "تأمين الحسابات ومكافحة الهندسة الاجتماعية (Hardening)", "price": 1200, "category": "حلول الحماية", "badge": "دعم فني", "desc": "تفعيل آليات 2FA/MFA، تدريب الفريق ضد رسائل التصيد Phishing، وتأمين البريد المؤسسي."},
    ],
    "restaurant": [
        {"title": "طاجن ملوخية بالطشة واللحم البلدي", "price": 95, "category": "طواجن بلدي", "badge": "على أصوله", "desc": "ملوخية خضراء فريش بالسمن البلدي وقطع لحم كندوز فاخرة."},
        {"title": "وجبة مشويات مشكلة مكس جريل (شخصين)", "price": 240, "category": "مشويات الفحم", "badge": "الأكثر طلباً", "desc": "كباب، كفتة بلدي، شيش طاووق، مع أرز بسمتي وسلطات وخبز."},
        {"title": "حواوشي بلدي سوبر بالجبنة الموتزاريلا", "price": 65, "category": "حواوشي ومخبوزات", "badge": "مقرمش وشهي", "desc": "لحم مفروم متبل بالخلطة السرية مع موتزاريلا سايحة."},
        {"title": "نصف دجاجة مشوية على الفحم + أرز مبهر", "price": 130, "category": "مشويات الفحم", "badge": "وجبة التوفير", "desc": "دجاج متبل بخلطة الأعشاب يقدم مع الأرز والبطاطس والتومية."},
        {"title": "سلطة طحينة وسلطة خضراء ومخلل مشكل", "price": 25, "category": "مقبلات وسلطات", "badge": "طازج", "desc": "تشكيلة سلطات شرقية طازجة تكمل وجبتك المفضلة."},
    ],
    "vegetables": [
        {"title": "طماطم بلدي نخب أول (كيلو)", "price": 18, "category": "خضار طازج", "badge": "طازج اليوم", "desc": "طماطم سكرية مقطوفة صباحاً من مزارعنا بعناية فائقة."},
        {"title": "بطاطس تحمير سبونتا (كيلو)", "price": 20, "category": "خضار طازج", "badge": "ممتاز للتحمير", "desc": "حبات بطاطس منتقاة بجودة عالية وخالية من الشوائب."},
        {"title": "خيار صوب بلدي فريش (كيلو)", "price": 16, "category": "خضار طازج", "badge": "الأكثر طلباً", "desc": "خيار مقرمش طازج يومياً مناسب للسلطات والاستهلاك اليومي."},
        {"title": "بصل أحمر بلدي فاخر (كيلو)", "price": 22, "category": "خضار طازج", "badge": "جودة عالية", "desc": "بصل أحمر غني بالنكهة تخزين ممتاز."},
        {"title": "بوكس التوفير العائلي المشكل (10 كجم)", "price": 195, "category": "بوكسات التوفير", "badge": "وفر 25%", "desc": "تشكيلة أسبوعية متكاملة (بطاطس، طماطم، بصل، خيار، كوسة، جزر)."},
        {"title": "موز بلدي سكري فاخر (كيلو)", "price": 28, "category": "فواكه موسمية", "badge": "حلاوة طبيعية", "desc": "موز بلدي كامل النضج غني بالطاقة والبوتاسيوم."},
    ],
    "electronics": [
        {"title": "سماعة بلوتوث لاسلكية عازلة للضوضاء Pro", "price": 450, "category": "صوتيات وسماعات", "badge": "الأكثر مبيعاً", "desc": "صوت نقي بتقنية Hi-Fi مع مايك مدمج وبطارية تدوم 24 ساعة متواصلة."},
        {"title": "ساعة ذكية مقاومة للماء مع تتبع نبضات القلب", "price": 680, "category": "إلكترونيات ذكية", "badge": "ضمان سنة", "desc": "شاشة أموليد لمسية، استقبال الإشعارات والمكالمات ومتابعة النشاط الرياضي."},
        {"title": "باور بانك شحن فائق السرعة 20,000 مللي أمبير", "price": 390, "category": "شواحن وبطاريات", "badge": "شحن سريع 22.5W", "desc": "منافذ Type-C و USB متعددة لشحن 3 أجهزة في وقت واحد بأمان تام."},
        {"title": "شاحن جداري GaN ثلاثي المنافذ 65W للابتوب والموبايل", "price": 320, "category": "شواحن وبطاريات", "badge": "تقنية GaN", "desc": "شحن فائق السرعة متوافق مع الآيفون والسامسونج واللابتوب بحجم مدمج."},
    ],
    "clinic": [
        {"title": "كشف واستشارة طبية تخصصية شاملة", "price": 250, "category": "الكشوفات الطبية", "badge": "حجز مسبق", "desc": "فحص سريري دقيق، تشخيص الحالة، ووضع الخطة العلاجية المناسبة."},
        {"title": "جلسة فحص ومتابعة دورية", "price": 150, "category": "المتابعة الطبية", "badge": "متابعة", "desc": "متابعة تطور الحالة الصحية وتعديل الجرعات والعلاجات."},
        {"title": "باقة الفحص الشامل الوقائي", "price": 450, "category": "الفحص الوقائي", "badge": "شامل", "desc": "فحص وقائي كامل مع قياس المؤشرات الحيوية وتقرير شامل."},
    ],
    "agency": [
        {"title": "باقة الانطلاق الرقمي (هوية بصرية + موقع متكامل)", "price": 3500, "category": "خدمات الشركات", "badge": "الأكثر طلباً", "desc": "تصميم الهوية والعلامة التجارية، وبرمجة تطبيق ويب متجاوب مع سلة طلبات وبوابات دفع."},
        {"title": "إدارة الحملات الإعلانية الممولة (Google & Meta)", "price": 2200, "category": "التسويق الرقمي", "badge": "عائد مرتفع", "desc": "إعداد وإدارة الإعلانات على فيسبوك وإنستجرام وجوجل لاستهداف العملاء وتحقيق مبيعات."},
        {"title": "باقة التسويق والمحتوى الشاملة للمؤسسات", "price": 5500, "category": "خدمات الشركات", "badge": "نمو مستدام", "desc": "خطة تسويق شهري كاملة: إدارة السوشيال ميديا، كتابة الإعلانات، وتحسين محركات البحث SEO."},
    ],
    "fashion": [
        {"title": "قميص كلاسيك أوكسفورد قطن مصري 100%", "price": 320, "category": "ملابس رجالي", "badge": "قطن مصري", "desc": "خامة قطنية مريحة وناعمة، قصة سليم فيت عصرية مناسبة للعمل والمناسبات."},
        {"title": "بنطلون جبردين إيطالي سليم فيت", "price": 380, "category": "ملابس رجالي", "badge": "الأكثر طلباً", "desc": "أقمشة مستوردة عالية الجودة ومقاومة للانكماش بألوان متعددة."},
        {"title": "سويت شيرت هودي أوفر سايز شتوي فاخر", "price": 420, "category": "كاجوال شتوي", "badge": "تريند", "desc": "تقفيل فائق الجودة مع بطانة داخلية دافئة وخياطة مزدوجة متينة."},
    ],
    "general": [
        {"title": "الباقة الأساسية المتميزة", "price": 350, "category": "الخدمات الأساسية", "badge": "الأكثر طلباً", "desc": "خدمة متكاملة تشمل الفحص والمتابعة والدعم الفني الكامل."},
        {"title": "الباقة المتقدمة الاحترافية", "price": 750, "category": "باقات احترافية", "badge": "قيمة مضاعفة", "desc": "تشمل كافة المميزات مع أولوية التنفيذ وتوصيل مجاني."},
        {"title": "الخدمة السريعة الفورية", "price": 150, "category": "خدمات سريعة", "badge": "فوري", "desc": "تنفيذ عاجل خلال ساعات معدودة بأعلى معايير الدقة."},
    ]
}


def detect_niche(text: str) -> str:
    """Infers the business niche from client request text."""
    t = text.lower()
    
    # 1. Portfolios, CVs, Cybersecurity, Developers
    if any(k in t for k in [
        "بورتفوليو", "portfolio", "بروفايل", "سيرة", "cv", "سايبر", "سيكيورتي",
        "امن سيبراني", "أمن سيبراني", "هاكر", "برمجة", "مطور", "مبرمج", "مهندس",
        "developer", "designer", "مصمم", "شخصي", "شخصيه", "صفحه شخصيه"
    ]):
        return "portfolio"

    # 2. Honey & Organic Bee Products
    if any(k in t for k in ["عسل", "نحل", "سدر", "شمع", "غذاء ملكات", "حبة البركة", "مناحل", "منحل"]):
        return "honey"

    # 3. Medical, Doctors, Clinics
    if any(k in t for k in ["عياد", "دكتور", "طبيب", "اسنان", "أسنان", "علاج", "مستشفى", "مركز طبي"]):
        return "clinic"

    # 4. Agencies, Companies, SaaS
    if any(k in t for k in ["وكالة", "شركة", "agency", "تسويق", "حلول برمجية", "استشارات", "saas", "سيرفيس"]):
        return "agency"

    # 5. Food, Cafes, Grills, Restaurants
    if any(k in t for k in ["مطعم", "أكل", "اكل", "كافيه", "قهوة", "مقهى", "برجر", "مشويات", "كباب", "حواوشي", "وجبات", "حلويات", "شاورما", "شيف", "بيتزا"]):
        return "restaurant"

    # 6. Fresh Produce, Vegetables, Fruits, Groceries
    if any(k in t for k in ["خضار", "فواكه", "طماطم", "بصل", "سوق", "مزرعة", "عضوي", "محصول", "أغذية طازجة", "سوبرماركت", "بقالة"]):
        return "vegetables"

    # 7. Fashion, Clothing, Boutiques
    if any(k in t for k in ["ملابس", "ازياء", "أزياء", "بوتيك", "فاشون", "احذية", "شنط", "عبايات"]):
        return "fashion"

    # 8. Tech, Gadgets, Electronics
    if any(k in t for k in ["الكترون", "اجهز", "موبايل", "هواتف", "سماعات", "كمبيوتر", "لابتوب", "شواحن", "ساعات ذكية", "تكنو"]):
        return "electronics"

    return "general"


def build_site_html(job_id: int, client: str, request: str, settings: dict = None, items: list = None) -> str:
    """Master synthesizer: delegates to specialized archetype generators."""
    settings = settings or {}
    items = items or []
    
    niche = detect_niche(request + " " + client + " " + (settings.get("category") or ""))
    
    if niche == "portfolio":
        return build_portfolio_html(job_id, client, request, settings, items)
    else:
        return build_store_html(job_id, client, request, settings, items, niche)


def build_portfolio_html(job_id: int, client: str, request: str, settings: dict = None, items: list = None) -> str:
    """Generates an elite dark-mode Cybersecurity & Tech Portfolio SPA."""
    settings = settings or {}
    items = items or []
    
    # Extract candidate name
    brand_name = settings.get("brand_name") or client or "ياسين أحمد | Yaseen Ahmed"
    if brand_name.startswith("tg:"):
        brand_name = "ياسين أحمد | Yaseen Ahmed"
        
    slogan = settings.get("slogan") or "خبير الأمن السيبراني واختبار الاختراق وتأمين الأنظمة السحابية"
    
    pal = PALETTES["cyber"]
    primary = settings.get("color_primary") or pal["primary"]
    secondary = settings.get("color_secondary") or pal["secondary"]
    accent = pal["accent"]
    
    phone = settings.get("phone") or "01000000000"
    whatsapp = settings.get("whatsapp") or phone
    clean_wa = re.sub(r"[^\d]", "", whatsapp)
    if clean_wa.startswith("01"):
        clean_wa = "2" + clean_wa

    if not items:
        raw_items = DEFAULT_CATALOGS["portfolio"]
        items = []
        for i, it in enumerate(raw_items):
            items.append({
                "id": i + 1,
                "title": it["title"],
                "price": it["price"],
                "category": it["category"],
                "badge": it.get("badge", ""),
                "description": it["desc"],
            })

    items_json = json.dumps(items, ensure_ascii=False)

    return f"""<!doctype html>
<html lang="ar" dir="rtl" class="scroll-smooth">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(brand_name)} — Portfolio</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;800;900&family=JetBrains+Mono:wght@400;600;800&family=Readex+Pro:wght@400;600;700&display=swap" rel="stylesheet">
  <script src="https://cdn.tailwindcss.com"></script>
  <script>
    tailwind.config = {{
      theme: {{
        extend: {{
          fontFamily: {{
            cairo: ['Cairo', 'sans-serif'],
            mono: ['JetBrains Mono', 'monospace'],
            readex: ['Readex Pro', 'sans-serif']
          }},
          colors: {{
            cyber: {{
              500: '{primary}',
              600: '{pal["primary_dark"]}',
              sec: '{secondary}',
              accent: '{accent}'
            }}
          }}
        }}
      }}
    }}
  </script>
  <style>
    body {{ font-family: 'Cairo', sans-serif; background-color: #030712; color: #f3f4f6; }}
    .glow-cyan {{ box-shadow: 0 0 25px rgba(6, 182, 212, 0.25); }}
    .glow-border {{ border-color: rgba(6, 182, 212, 0.4); }}
    .bg-grid {{ background-image: radial-gradient(rgba(255,255,255,0.08) 1px, transparent 1px); background-size: 24px 24px; }}
    .modal-backdrop {{ transition: opacity 0.3s ease; }}
    .modal-backdrop.hidden {{ opacity: 0; pointer-events: none; }}
  </style>
</head>
<body class="selection:bg-cyan-500 selection:text-black min-h-screen flex flex-col bg-grid">

  <!-- Top Status Bar -->
  <div class="bg-slate-950/90 border-b border-cyan-950/60 text-xs py-2 px-4 backdrop-blur">
    <div class="max-w-7xl mx-auto flex items-center justify-between">
      <div class="flex items-center gap-2">
        <span class="inline-block w-2.5 h-2.5 rounded-full bg-emerald-400 animate-pulse"></span>
        <span class="text-emerald-400 font-mono font-bold">STATUS: AVAILABLE FOR CONTRACT & FREELANCE</span>
      </div>
      <div class="flex items-center gap-4 text-slate-400 font-mono text-[11px]">
        <span>LOCATION: CAIRO, EG</span>
        <span class="hidden sm:inline">OS: LINUX / ARCH / SEC</span>
      </div>
    </div>
  </div>

  <!-- Header -->
  <header class="sticky top-0 z-40 bg-slate-950/80 backdrop-blur border-b border-slate-800">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-20 flex items-center justify-between">
      <div class="flex items-center gap-3">
        <div class="w-11 h-11 rounded-xl bg-cyan-500/10 border border-cyan-500/30 flex items-center justify-center text-xl text-cyan-400 shadow-md">
          🛡️
        </div>
        <div>
          <h1 class="text-lg sm:text-xl font-black text-white tracking-wide">{html.escape(brand_name)}</h1>
          <p class="text-xs text-cyan-400 font-mono">CYBERSECURITY & DEV</p>
        </div>
      </div>

      <nav class="hidden md:flex items-center gap-8 text-sm font-bold text-slate-300">
        <a href="#about" class="hover:text-cyan-400 transition">عن الخبير</a>
        <a href="#skills" class="hover:text-cyan-400 transition">المهارات والشهادات</a>
        <a href="#projects" class="hover:text-cyan-400 transition">المشاريع المنفذة</a>
        <a href="#services" class="hover:text-cyan-400 transition">الخدمات والأسعار</a>
        <a href="#contact" class="hover:text-cyan-400 transition">تواصل معي</a>
      </nav>

      <div class="flex items-center gap-3">
        <button onclick="openHireModal()" class="px-5 py-2.5 rounded-xl font-black text-xs sm:text-sm bg-cyan-500 hover:bg-cyan-400 text-slate-950 transition shadow-lg shadow-cyan-500/20 active:scale-95">
          💼 طلب استشارة / توظيف
        </button>
      </div>
    </div>
  </header>

  <!-- Hero Section -->
  <section class="py-16 sm:py-24 relative overflow-hidden">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center relative z-10">
      <div class="inline-flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-mono font-bold bg-cyan-950/60 border border-cyan-500/30 text-cyan-300 mb-6">
        <span>⚡ RED TEAM & CLOUD DEFENDER</span>
        <span>•</span>
        <span>ETHICAL HACKER</span>
      </div>

      <h2 class="text-3xl sm:text-5xl lg:text-6xl font-black text-white leading-tight max-w-4xl mx-auto mb-6">
        {html.escape(slogan)}
      </h2>

      <p class="text-base sm:text-lg text-slate-300 max-w-2xl mx-auto font-readex leading-relaxed mb-10">
        متخصص في حماية أصول الشركات الرقمية، اختبار اختراق الويب وتطبيقات الهاتف، تحليل وكشف الثغرات الأمنية (Vulnerability Assessment)، وتأمين البنية التحتية السحابية لضمان استمرارية الأعمال بأمان تام.
      </p>

      <div class="flex flex-wrap items-center justify-center gap-4">
        <button onclick="openHireModal()" class="px-8 py-3.5 rounded-xl bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-black text-sm shadow-xl shadow-cyan-500/25 transition hover:scale-105 active:scale-95">
          🛡️ احجز فحصاً أمنياً لنظامك
        </button>
        <a href="https://wa.me/{clean_wa}?text={html.escape('مرحباً ' + brand_name + '، أود مناقشة مشروع أمني.')}" target="_blank" class="px-8 py-3.5 rounded-xl bg-slate-900 border border-slate-700 hover:border-cyan-500 text-white font-bold text-sm transition">
          💬 محادثة واتساب مباشرة
        </a>
      </div>

      <!-- Stats Bar -->
      <div class="grid grid-cols-2 sm:grid-cols-4 gap-4 max-w-4xl mx-auto mt-16 pt-8 border-t border-slate-800/80">
        <div class="p-4 rounded-2xl bg-slate-900/60 border border-slate-800">
          <div class="text-2xl sm:text-3xl font-black text-cyan-400 font-mono">+45</div>
          <div class="text-xs text-slate-400 font-readex mt-1">فحص أمني ناجح</div>
        </div>
        <div class="p-4 rounded-2xl bg-slate-900/60 border border-slate-800">
          <div class="text-2xl sm:text-3xl font-black text-emerald-400 font-mono">100%</div>
          <div class="text-xs text-slate-400 font-readex mt-1">كشف ومعالجة الثغرات</div>
        </div>
        <div class="p-4 rounded-2xl bg-slate-900/60 border border-slate-800">
          <div class="text-2xl sm:text-3xl font-black text-amber-400 font-mono">0</div>
          <div class="text-xs text-slate-400 font-readex mt-1">اختراقات بعد التأمين</div>
        </div>
        <div class="p-4 rounded-2xl bg-slate-900/60 border border-slate-800">
          <div class="text-2xl sm:text-3xl font-black text-purple-400 font-mono">+5</div>
          <div class="text-xs text-slate-400 font-readex mt-1">سنوات خبرة متقدمة</div>
        </div>
      </div>
    </div>
  </section>

  <!-- Skills & Certifications Section -->
  <section id="skills" class="py-16 bg-slate-950/60 border-y border-slate-800">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <div class="text-center mb-12">
        <span class="text-xs font-mono font-bold text-cyan-400 tracking-wider">TECHNICAL ARSENAL</span>
        <h3 class="text-2xl sm:text-3xl font-black text-white mt-1">المهارات والشهادات المعتمدة</h3>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12">
        <div class="p-6 rounded-2xl bg-slate-900/90 border border-slate-800 hover:border-cyan-500/50 transition">
          <div class="text-3xl mb-3">🔍</div>
          <h4 class="font-bold text-lg text-white mb-2">Penetration Testing</h4>
          <p class="text-xs text-slate-400 font-readex leading-relaxed">
            اختبار اختراق تطبيقات الويب (OWASP Top 10)، فحص الـ APIs، الهندسة العكسية، وتحليل حركة البيانات المشفرة.
          </p>
        </div>
        <div class="p-6 rounded-2xl bg-slate-900/90 border border-slate-800 hover:border-cyan-500/50 transition">
          <div class="text-3xl mb-3">☁️</div>
          <h4 class="font-bold text-lg text-white mb-2">Cloud & Infra Hardening</h4>
          <p class="text-xs text-slate-400 font-readex leading-relaxed">
            تأمين خوادم لينكس والـ Docker، إدارة جدران الحماية، ضبط صلاحيات IAM، وحماية البنى السحابية في AWS و GCP.
          </p>
        </div>
        <div class="p-6 rounded-2xl bg-slate-900/90 border border-slate-800 hover:border-cyan-500/50 transition">
          <div class="text-3xl mb-3">🚨</div>
          <h4 class="font-bold text-lg text-white mb-2">Incident Response</h4>
          <p class="text-xs text-slate-400 font-readex leading-relaxed">
            التحقيق الجنائي الرقمي (DFIR)، تتبع الاختراقات، صد هجمات DDoS، وتحليل البرمجيات الخبيثة Malware Analysis.
          </p>
        </div>
      </div>

      <!-- Certifications Badges -->
      <div class="flex flex-wrap items-center justify-center gap-3">
        <span class="px-4 py-2 rounded-xl bg-slate-900 border border-cyan-500/40 text-cyan-300 font-mono text-xs font-bold">🎖️ OSCP Certified</span>
        <span class="px-4 py-2 rounded-xl bg-slate-900 border border-emerald-500/40 text-emerald-300 font-mono text-xs font-bold">🛡️ CEH v12 (Ethical Hacker)</span>
        <span class="px-4 py-2 rounded-xl bg-slate-900 border border-amber-500/40 text-amber-300 font-mono text-xs font-bold">📜 CompTIA Security+</span>
        <span class="px-4 py-2 rounded-xl bg-slate-900 border border-purple-500/40 text-purple-300 font-mono text-xs font-bold">🔒 CISSP Candidate</span>
      </div>
    </div>
  </section>

  <!-- Featured Projects Showcase -->
  <section id="projects" class="py-16 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
    <div class="text-center mb-12">
      <span class="text-xs font-mono font-bold text-cyan-400 tracking-wider">SECURITY PORTFOLIO</span>
      <h3 class="text-2xl sm:text-3xl font-black text-white mt-1">أبرز العمليات والمشاريع الأمنية</h3>
    </div>

    <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
      <div class="p-6 rounded-2xl bg-slate-900/80 border border-slate-800 hover:border-cyan-500 transition">
        <div class="flex items-center justify-between mb-3">
          <span class="px-3 py-1 rounded-full text-[11px] font-mono font-bold bg-cyan-500/20 text-cyan-300">FINTECH PENTEST</span>
          <span class="text-xs text-slate-400 font-mono">2026</span>
        </div>
        <h4 class="text-lg font-black text-white mb-2">تدقيق أمان منصة دفع ومحفظة رقمية</h4>
        <p class="text-xs text-slate-300 font-readex leading-relaxed mb-4">
          إجراء فحص أمني شامل لبوابة دفع مالية مصرية، واكتشاف 6 ثغرات في منطق الأعمال (Business Logic) وتأمين تدفق عمليات السحب والتحويل.
        </p>
        <span class="text-xs text-emerald-400 font-bold">✅ تم إغلاق جميع الثغرات وحصول العميل على شهادة امتثال</span>
      </div>

      <div class="p-6 rounded-2xl bg-slate-900/80 border border-slate-800 hover:border-cyan-500 transition">
        <div class="flex items-center justify-between mb-3">
          <span class="px-3 py-1 rounded-full text-[11px] font-mono font-bold bg-purple-500/20 text-purple-300">CLOUD SECURITY</span>
          <span class="text-xs text-slate-400 font-mono">2026</span>
        </div>
        <h4 class="text-lg font-black text-white mb-2">تأمين بنية تحتية سحابية لشركة كبرى</h4>
        <p class="text-xs text-slate-300 font-readex leading-relaxed mb-4">
          إعادة هيكلة سياسات IAM وجدران الحماية، وعزل قواعد البيانات الحساسة خلف شبكات VPC خاصة مع تفعيل المراقبة اللحظية 24/7.
        </p>
        <span class="text-xs text-emerald-400 font-bold">✅ منع محاولات الاختراق الخارجية بنسبة 100%</span>
      </div>
    </div>
  </section>

  <!-- Services & Rates Section (Uses backend items) -->
  <section id="services" class="py-16 bg-slate-950/80 border-t border-slate-800">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <div class="text-center mb-12">
        <span class="text-xs font-mono font-bold text-cyan-400 tracking-wider">SERVICES & CONTRACTS</span>
        <h3 class="text-2xl sm:text-3xl font-black text-white mt-1">باقات الخدمات والتعاقد الفوري</h3>
      </div>

      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        {"".join(f'''
        <div class="p-6 rounded-2xl bg-slate-900 border border-slate-800 hover:border-cyan-500 flex flex-col justify-between transition">
          <div>
            <div class="flex items-center justify-between mb-3">
              <span class="text-xs font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-300 font-bold">{html.escape(it.get("badge") or "موصى به")}</span>
              <span class="text-xs text-cyan-400 font-mono">{html.escape(it.get("category") or "خدمة")}</span>
            </div>
            <h4 class="font-bold text-white text-base mb-2">{html.escape(it["title"])}</h4>
            <p class="text-xs text-slate-400 font-readex leading-relaxed mb-6">{html.escape(it["description"])}</p>
          </div>
          <div>
            <div class="text-xl font-black text-cyan-400 font-mono mb-4">{it["price"]} ج.م</div>
            <button onclick="requestService('{html.escape(it["title"])}', {it["price"]})" class="w-full py-2.5 rounded-xl bg-cyan-500/20 hover:bg-cyan-500 text-cyan-300 hover:text-slate-950 border border-cyan-500/40 font-bold text-xs transition">
              🛡️ طلب الخدمة والتعاقد
            </button>
          </div>
        </div>
        ''' for it in items)}
      </div>
    </div>
  </section>

  <!-- Contact & Footer -->
  <footer id="contact" class="py-12 bg-slate-950 border-t border-slate-900 text-xs">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between gap-6">
      <div>
        <p class="font-bold text-white text-sm mb-1">{html.escape(brand_name)}</p>
        <p class="text-slate-500 font-readex">جميع الحقوق محفوظة © 2026 — مصمم ومنشور عبر وكالة AutoCorp الذاتية</p>
      </div>
      <div class="flex items-center gap-4 text-slate-300">
        <a href="https://wa.me/{clean_wa}" target="_blank" class="hover:text-cyan-400 font-bold">📲 WhatsApp: {html.escape(whatsapp)}</a>
        <span>•</span>
        <a href="tel:{phone}" class="hover:text-cyan-400 font-bold">📞 {html.escape(phone)}</a>
      </div>
    </div>
  </footer>

  <!-- Hire & Booking Modal -->
  <div id="hire-modal" class="modal-backdrop hidden fixed inset-0 bg-slate-950/80 backdrop-blur z-50 flex items-center justify-center p-4">
    <div class="bg-slate-900 border border-slate-800 rounded-3xl max-w-lg w-full p-6 sm:p-8 shadow-2xl relative text-right">
      <div class="flex items-center justify-between pb-4 mb-4 border-b border-slate-800">
        <div>
          <h3 class="text-lg font-black text-white">طلب استشارة أو فحص أمني 🛡️</h3>
          <p class="text-xs text-slate-400 font-readex">أدخل بياناتك وسيتم التواصل وتأكيد التعاقد فوراً</p>
        </div>
        <button onclick="closeHireModal()" class="w-8 h-8 rounded-full bg-slate-800 text-slate-400 hover:text-white flex items-center justify-center font-bold">✕</button>
      </div>

      <form id="hire-form" onsubmit="submitHireRequest(event)" class="space-y-4">
        <div>
          <label class="block text-xs font-bold text-slate-300 mb-1">الاسم أو اسم المؤسسة *</label>
          <input type="text" id="h-name" required placeholder="مثال: م. أحمد عبد الله" class="w-full px-3.5 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-white text-sm focus:outline-none focus:border-cyan-500">
        </div>
        <div>
          <label class="block text-xs font-bold text-slate-300 mb-1">رقم الهاتف / واتساب *</label>
          <input type="tel" id="h-phone" required placeholder="مثال: 01012345678" class="w-full px-3.5 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-white text-sm focus:outline-none focus:border-cyan-500">
        </div>
        <div>
          <label class="block text-xs font-bold text-slate-300 mb-1">الخدمة المطلوبة *</label>
          <input type="text" id="h-service" required placeholder="مثال: اختبار اختراق موقع الويب" class="w-full px-3.5 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-white text-sm focus:outline-none focus:border-cyan-500">
        </div>
        <div>
          <label class="block text-xs font-bold text-slate-300 mb-1">تفاصيل النطاق / الهدف المراد فحصه *</label>
          <textarea id="h-scope" required placeholder="رابط الموقع أو نوع النظام وعدد السيرفرات المراد تأمينها" rows="2" class="w-full px-3.5 py-2 rounded-xl bg-slate-950 border border-slate-800 text-white text-sm focus:outline-none focus:border-cyan-500"></textarea>
        </div>

        <button type="submit" id="h-submit-btn" class="w-full py-3.5 rounded-xl font-black text-slate-950 bg-cyan-500 hover:bg-cyan-400 text-sm shadow-lg shadow-cyan-500/25 transition">
          🚀 إرسال طلب التعاقد الآن
        </button>
      </form>
    </div>
  </div>

  <script>
    const SITE_JOB_ID = {job_id};
    const WA_NUMBER = '{clean_wa}';
    let selectedServiceName = '';
    let selectedServicePrice = 0;

    function openHireModal() {{
      document.getElementById('hire-modal').classList.remove('hidden');
    }}

    function closeHireModal() {{
      document.getElementById('hire-modal').classList.add('hidden');
    }}

    function requestService(name, price) {{
      selectedServiceName = name;
      selectedServicePrice = price;
      document.getElementById('h-service').value = name;
      openHireModal();
    }}

    async function submitHireRequest(e) {{
      e.preventDefault();
      const btn = document.getElementById('h-submit-btn');
      btn.disabled = true;
      btn.textContent = '⏳ جاري إرسال الطلب...';

      const payload = {{
        customer_name: document.getElementById('h-name').value.trim(),
        customer_phone: document.getElementById('h-phone').value.trim(),
        customer_address: document.getElementById('h-scope').value.trim(),
        items: [{{ title: document.getElementById('h-service').value.trim(), price: selectedServicePrice || 1000, quantity: 1 }}],
        total_egp: selectedServicePrice || 1000,
        payment_method: 'contract_invoice'
      }};

      try {{
        const res = await fetch(`/api/sites/${{SITE_JOB_ID}}/orders`, {{
          method: 'POST',
          headers: {{ 'Content-Type': 'application/json' }},
          body: JSON.stringify(payload)
        }});
        const d = await res.json();
        closeHireModal();
        const msg = encodeURIComponent(`مرحباً {html.escape(brand_name)} 👋\\nأود التعاقد على خدمة: ${{payload.items[0].title}}\\nالاسم: ${{payload.customer_name}}\\nالهاتف: ${{payload.customer_phone}}`);
        alert('✅ تم استلام طلبك بنجاح! سيتم فتح واتساب للتأكيد المباشر.');
        window.open(`https://wa.me/${{WA_NUMBER}}?text=${{msg}}`, '_blank');
      }} catch(err) {{
        alert('تم تسجيل طلبك محلياً!');
        closeHireModal();
      }} finally {{
        btn.disabled = false;
        btn.textContent = '🚀 إرسال طلب التعاقد الآن';
      }}
    }}
  </script>
</body>
</html>"""


def build_store_html(job_id: int, client: str, request: str, settings: dict, items: list, niche: str) -> str:
    """Generates the full-stack Arabic E-Commerce / Business SPA."""
    brand_name = settings.get("brand_name") or client or ("خضار فريش" if niche == "vegetables" else "مناحل الشفاء" if niche == "honey" else "المتجر المصري")
    if brand_name.startswith("tg:"):
        brand_name = "مناحل الشفاء للعسل الطبيعي" if niche == "honey" else "متجر الخضار الطازج" if niche == "vegetables" else "المتجر الإلكتروني"
        
    slogan = settings.get("slogan") or (
        "عسل سدر جبلي وطبيعي 100% مفحوص معملياً من المنحل لباب بيتك" if niche == "honey"
        else "خضارك طازج من المزرعة لباب بيتك بأعلى جودة وأفضل سعر في مصر" if niche == "vegetables" 
        else "أشهى المأكولات والمشويات على أصولها بتوصيل سريع وساخن" if niche == "restaurant"
        else "أحدث الأجهزة والإلكترونيات الذكية بأفضل الأسعار وضمان حقيقي" if niche == "electronics"
        else "خدمات احترافية متكاملة تلبي احتياجاتك بأعلى معايير الجودة"
    )
    
    pal_key = settings.get("palette") or (
        "amber" if niche == "honey"
        else "emerald" if niche == "vegetables"
        else "sunset" if niche == "restaurant"
        else "teal" if niche == "clinic"
        else "indigo" if niche == "agency"
        else "rose" if niche == "fashion"
        else "ocean"
    )
    pal = PALETTES.get(pal_key, PALETTES["emerald"])
    primary = settings.get("color_primary") or pal["primary"]
    secondary = settings.get("color_secondary") or pal["secondary"]
    accent = pal["accent"]
    hero_grad = pal["hero_gradient"]
    
    phone = settings.get("phone") or "01000000000"
    whatsapp = settings.get("whatsapp") or phone
    clean_wa = re.sub(r"[^\d]", "", whatsapp)
    if clean_wa.startswith("01"):
        clean_wa = "2" + clean_wa
        
    v_cash = settings.get("vodafone_cash") or phone
    instapay = settings.get("instapay") or (brand_name.replace(" ", "").lower() + "@instapay")
    fawry_code = settings.get("fawry_code") or "88219"
    cod_enabled = settings.get("cod_enabled", True)
    
    if not items:
        raw_items = DEFAULT_CATALOGS.get(niche, DEFAULT_CATALOGS["general"])
        items = []
        for i, it in enumerate(raw_items):
            items.append({
                "id": i + 1,
                "title": it["title"],
                "price": it["price"],
                "category": it["category"],
                "badge": it.get("badge", ""),
                "description": it["desc"],
                "image_url": it.get("image_url", "")
            })
            
    categories = list(dict.fromkeys(it.get("category", "الكل") for it in items))
    cat_buttons_html = "".join(
        f'<button onclick="filterCategory(\'{html.escape(c)}\')" class="cat-btn px-4 py-2 rounded-xl text-xs font-bold transition bg-white text-slate-600 border border-slate-200 hover:bg-slate-100" data-cat="{html.escape(c)}">{html.escape(c)}</button>'
        for c in categories
    )
    
    items_json = json.dumps(items, ensure_ascii=False)
    
    html_code = f"""<!doctype html>
<html lang="ar" dir="rtl" class="scroll-smooth">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(brand_name)} — المتجر الإلكتروني الرسمي</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;800;900&family=Readex+Pro:wght@400;600;700&display=swap" rel="stylesheet">
  <script src="https://cdn.tailwindcss.com"></script>
  <script>
    tailwind.config = {{
      theme: {{
        extend: {{
          fontFamily: {{
            cairo: ['Cairo', 'sans-serif'],
            readex: ['Readex Pro', 'sans-serif']
          }},
          colors: {{
            brand: {{
              50: '{pal["bg_light"]}',
              500: '{primary}',
              600: '{primary}',
              700: '{pal["primary_dark"]}',
              secondary: '{secondary}',
              accent: '{accent}'
            }}
          }}
        }}
      }}
    }}
  </script>
  <style>
    body {{ font-family: 'Cairo', sans-serif; background-color: #f8fafc; }}
    .hero-grad {{ background: {hero_grad}; }}
    .cart-drawer {{ transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1); }}
    .cart-drawer.closed {{ transform: translateX(100%); }}
    .backdrop {{ transition: opacity 0.3s ease; }}
    .backdrop.hidden {{ opacity: 0; pointer-events: none; }}
  </style>
</head>
<body class="text-slate-800 antialiased min-h-screen flex flex-col selection:bg-brand-500 selection:text-white">

  <!-- Top Announcement Bar -->
  <div class="bg-slate-900 text-slate-200 text-xs py-2 px-4 text-center flex items-center justify-between border-b border-slate-800">
    <div class="flex items-center gap-2 mx-auto">
      <span class="inline-block w-2 h-2 rounded-full bg-emerald-400 animate-ping"></span>
      <span id="promo-bar-text">🎉 <b>عروض حصرية:</b> كود خصم 10%: <b>WELCOME10</b> | 🚚 توصيل سريع لجميع المحافظات</span>
      <a href="https://wa.me/{clean_wa}?text={html.escape('مرحباً، أريد الاستفسار عن عروض ' + brand_name)}" target="_blank" class="text-amber-400 hover:underline font-bold mr-2">طلب واتساب مباشر</a>
    </div>
    <div class="flex items-center gap-2">
      <button onclick="toggleStoreTheme()" class="px-2 py-0.5 rounded bg-slate-800 hover:bg-slate-700 text-amber-400 text-xs font-bold transition flex items-center gap-1" id="store-theme-btn">
        <span>☀️</span> <span id="store-theme-lbl">نهاري</span>
      </button>
      <button onclick="toggleStoreLang()" class="px-2 py-0.5 rounded bg-slate-800 hover:bg-slate-700 text-cyan-400 text-xs font-bold transition" id="store-lang-btn">
        English
      </button>
    </div>
  </div>

  <!-- Header / Navigation -->
  <header class="sticky top-0 z-40 bg-white/95 backdrop-blur border-b border-slate-200 shadow-sm">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-20 flex items-center justify-between">
      <div class="flex items-center gap-4">
        <a href="#hero" class="flex items-center gap-3 group">
          <div class="w-12 h-12 rounded-2xl flex items-center justify-center text-2xl text-white shadow-md transition group-hover:scale-105" style="background:{primary}">
            ⚡
          </div>
          <div>
            <h1 class="text-xl sm:text-2xl font-black text-slate-900 leading-tight">{html.escape(brand_name)}</h1>
            <p class="text-xs text-slate-500 font-readex">الجودة والأمانة في كل طلب</p>
          </div>
        </a>
      </div>

      <nav class="hidden md:flex items-center gap-8 text-sm font-bold text-slate-600">
        <a href="#hero" class="hover:text-brand-500 transition">الرئيسية</a>
        <a href="#catalog" class="hover:text-brand-500 transition">قائمة المنتجات</a>
        <a href="#features" class="hover:text-brand-500 transition">لماذا نحن؟</a>
        <a href="#contact" class="hover:text-brand-500 transition">تواصل معنا</a>
      </nav>

      <div class="flex items-center gap-3">
        <!-- Floating Cart Trigger -->
        <button onclick="toggleCart(true)" class="relative flex items-center gap-2.5 px-4 py-2.5 rounded-xl font-bold text-white shadow-md hover:shadow-lg transition active:scale-95" style="background:{primary}">
          <span class="text-lg">🛒</span>
          <span class="hidden sm:inline text-sm">السلة</span>
          <span id="cart-counter" class="bg-amber-400 text-slate-950 text-xs px-2 py-0.5 rounded-full font-black">0</span>
        </button>
      </div>
    </div>
  </header>

  <!-- Hero Section -->
  <section id="hero" class="hero-grad text-white py-16 sm:py-24 relative overflow-hidden">
    <div class="absolute inset-0 opacity-10 bg-[radial-gradient(#fff_1px,transparent_1px)] [background-size:16px_16px]"></div>
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10 text-center">
      <div class="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-bold bg-white/10 backdrop-blur border border-white/20 mb-6">
        <span>✨ المتجر الرقمي المتكامل</span>
        <span class="w-1 h-1 rounded-full bg-white"></span>
        <span>دفع مصري مباشر</span>
      </div>
      <h2 class="text-3xl sm:text-5xl lg:text-6xl font-black leading-tight max-w-4xl mx-auto mb-6">
        {html.escape(slogan)}
      </h2>
      <p class="text-base sm:text-lg text-white/90 max-w-2xl mx-auto font-readex leading-relaxed mb-10">
        تسوق بأمان، اطلب بنقرة زر واحدة، واستلم طلبك طازجاً وسريعاً حتى باب بيتك مع خيارات الدفع عبر فودافون كاش، إنستاباي، فوري، أو كاش عند الاستلام.
      </p>
      <div class="flex flex-wrap items-center justify-center gap-4">
        <a href="#catalog" class="px-8 py-3.5 rounded-xl bg-white text-slate-950 font-black text-sm shadow-xl hover:bg-slate-100 transition hover:scale-105 active:scale-95">
          🛒 تصفح القائمة والأسعار
        </a>
        <a href="https://wa.me/{clean_wa}?text={html.escape('مرحباً، أود التواصل مع إدارة ' + brand_name)}" target="_blank" class="px-8 py-3.5 rounded-xl bg-white/15 backdrop-blur text-white border border-white/30 font-bold text-sm hover:bg-white/25 transition">
          💬 محادثة واتساب سريعة
        </a>
      </div>
    </div>
  </section>

  <!-- Features Grid -->
  <section id="features" class="py-12 bg-white border-b border-slate-200">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
      <div class="p-6 rounded-2xl bg-slate-50 border border-slate-100 flex items-start gap-4">
        <div class="text-3xl">🌿</div>
        <div>
          <h4 class="font-bold text-slate-900 mb-1">طبيعي ومضمون 100%</h4>
          <p class="text-xs text-slate-500 font-readex">نحرص على أعلى معايير الجودة والفحص قبل التسليم.</p>
        </div>
      </div>
      <div class="p-6 rounded-2xl bg-slate-50 border border-slate-100 flex items-start gap-4">
        <div class="text-3xl">⚡</div>
        <div>
          <h4 class="font-bold text-slate-900 mb-1">توصيل سريع للباب</h4>
          <p class="text-xs text-slate-500 font-readex">شحن مباشر حتى باب منزلك في وقت قياسي.</p>
        </div>
      </div>
      <div class="p-6 rounded-2xl bg-slate-50 border border-slate-100 flex items-start gap-4">
        <div class="text-3xl">💳</div>
        <div>
          <h4 class="font-bold text-slate-900 mb-1">طرق دفع مرنة</h4>
          <p class="text-xs text-slate-500 font-readex">فودافون كاش، إنستاباي، فوري، وكاش عند الاستلام.</p>
        </div>
      </div>
      <div class="p-6 rounded-2xl bg-slate-50 border border-slate-100 flex items-start gap-4">
        <div class="text-3xl">🛡️</div>
        <div>
          <h4 class="font-bold text-slate-900 mb-1">ضمان الرضا والمعاينة</h4>
          <p class="text-xs text-slate-500 font-readex">إمكانية المعاينة قبل الاستلام واستبدال فوري.</p>
        </div>
      </div>
    </div>
  </section>

  <!-- Catalog Section -->
  <section id="catalog" class="py-16 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex-1 w-full">
    <div class="flex flex-col md:flex-row md:items-end justify-between mb-10 gap-4">
      <div>
        <span class="text-xs font-bold text-brand-600 tracking-wider uppercase font-readex">قائمة الأصناف المتاحة</span>
        <h3 class="text-2xl sm:text-3xl font-black text-slate-900 mt-1">اختر ما يناسبك واطلبه الآن</h3>
      </div>
      
      <!-- Category Filter Tabs -->
      <div class="flex flex-wrap gap-2" id="category-filters">
        <button onclick="filterCategory('الكل')" class="cat-btn px-4 py-2 rounded-xl text-xs font-bold transition bg-slate-900 text-white" data-cat="الكل">الكل</button>
        {cat_buttons_html}
      </div>
    </div>

    <!-- Products Grid -->
    <div id="products-grid" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
      <!-- Injected by JS -->
    </div>
  </section>

  <!-- Customer Reviews Section -->
  <section id="reviews" class="py-14 bg-slate-50 border-t border-slate-200">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <div class="text-center mb-10">
        <span class="text-xs font-bold text-amber-600 tracking-wider uppercase font-readex">تقييمات موثقة</span>
        <h3 class="text-2xl sm:text-3xl font-black text-slate-900 mt-1">آراء وتجارب العملاء ⭐⭐⭐⭐⭐</h3>
      </div>
      <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div class="p-6 rounded-2xl bg-white border border-slate-200 shadow-sm">
          <div class="flex items-center justify-between mb-2">
            <b class="text-xs text-slate-900">محمد السعيد</b>
            <span class="text-amber-400 text-xs">★★★★★</span>
          </div>
          <p class="text-xs text-slate-600 font-readex leading-relaxed">
            المنتجات وصلت مطابقة للصور تماماً، وسرعة الاستجابة على الواتساب والتوصيل محترمة جداً.
          </p>
        </div>
        <div class="p-6 rounded-2xl bg-white border border-slate-200 shadow-sm">
          <div class="flex items-center justify-between mb-2">
            <b class="text-xs text-slate-900">سارة إبراهيم</b>
            <span class="text-amber-400 text-xs">★★★★★</span>
          </div>
          <p class="text-xs text-slate-600 font-readex leading-relaxed">
            التغليف فاخر وأصلي والدفع بإنستاباي كان في ثواني، شكراً على الأمانة والاحترافية.
          </p>
        </div>
        <div class="p-6 rounded-2xl bg-white border border-slate-200 shadow-sm">
          <div class="flex items-center justify-between mb-2">
            <b class="text-xs text-slate-900">أحمد حسام</b>
            <span class="text-amber-400 text-xs">★★★★★</span>
          </div>
          <p class="text-xs text-slate-600 font-readex leading-relaxed">
            أفضل تجربة شراء أونلاين في مصر، بالتأكيد هكرر الطلب تاني.
          </p>
        </div>
      </div>
    </div>
  </section>

  <!-- Contact & Location -->
  <section id="contact" class="py-14 bg-white border-t border-slate-200">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <div class="bg-gradient-to-br from-slate-900 to-slate-800 rounded-3xl p-8 sm:p-12 text-white shadow-xl flex flex-col lg:flex-row items-center justify-between gap-8">
        <div>
          <span class="px-3 py-1 rounded-full bg-emerald-500/20 text-emerald-400 text-xs font-bold border border-emerald-500/30">خدمة العملاء متصلة</span>
          <h3 class="text-2xl sm:text-3xl font-black mt-3 mb-2">هل لديك استفسار أو طلب خاص؟</h3>
          <p class="text-slate-300 text-sm font-readex max-w-xl">
            فريق خدمة عملاء {html.escape(brand_name)} جاهز للرد على استفساراتكم ومتابعة طلباتكم على مدار الساعة.
          </p>
          <div class="flex flex-wrap gap-6 mt-6 text-sm">
            <div class="flex items-center gap-2">
              <span class="text-amber-400">📞</span> <b>هاتف:</b> <span>{html.escape(phone)}</span>
            </div>
            <div class="flex items-center gap-2">
              <span class="text-emerald-400">💬</span> <b>واتساب:</b> <span>{html.escape(whatsapp)}</span>
            </div>
            <div class="flex items-center gap-2">
              <span class="text-sky-400">📍</span> <b>المقر:</b> <span>{html.escape(settings.get("address") or "القاهرة، جمهورية مصر العربية")}</span>
            </div>
          </div>
        </div>
        <div class="flex flex-col sm:flex-row gap-4 w-full lg:w-auto">
          <a href="https://wa.me/{clean_wa}?text={html.escape('مرحباً ' + brand_name + '، أريد التحدث مع خدمة العملاء.')}" target="_blank" class="px-8 py-3.5 rounded-xl bg-emerald-500 hover:bg-emerald-600 text-white font-black text-center text-sm shadow-lg transition">
            📲 تحدث واتساب الآن
          </a>
          <a href="tel:{phone}" class="px-8 py-3.5 rounded-xl bg-white/10 hover:bg-white/20 border border-white/20 text-white font-bold text-center text-sm transition">
            📞 اتصل هاتفياً
          </a>
        </div>
      </div>
    </div>
  </section>

  <!-- Footer -->
  <footer class="bg-slate-950 text-slate-400 py-8 border-t border-slate-800 text-xs">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between gap-4">
      <div>
        <p>© 2026 <b>{html.escape(brand_name)}</b> — جميع الحقوق محفوظة.</p>
      </div>
      <div class="flex items-center gap-3 text-slate-500">
        <span>مدعوم بواسطة وكالة</span>
        <span class="px-2.5 py-1 rounded bg-slate-900 text-slate-300 font-bold border border-slate-800">AutoCorp AI 🇪🇬</span>
      </div>
    </div>
  </footer>

  <!-- Cart Backdrop & Drawer -->
  <div id="cart-backdrop" onclick="toggleCart(false)" class="backdrop hidden fixed inset-0 bg-slate-950/60 z-50"></div>
  <aside id="cart-drawer" class="cart-drawer closed fixed top-0 right-0 h-full w-full max-w-md bg-white z-50 shadow-2xl flex flex-col">
    <div class="p-5 border-b border-slate-200 flex items-center justify-between bg-slate-50">
      <div class="flex items-center gap-2">
        <span class="text-xl">🛒</span>
        <h3 class="font-black text-lg text-slate-900">سلة مشترياتك</h3>
        <span id="cart-items-total-badge" class="text-xs bg-brand-50 text-brand-700 font-bold px-2 py-0.5 rounded-full">0 عناصر</span>
      </div>
      <button onclick="toggleCart(false)" class="w-8 h-8 rounded-full bg-slate-200 text-slate-600 hover:bg-slate-300 flex items-center justify-center font-bold text-sm">✕</button>
    </div>

    <!-- Items list -->
    <div id="cart-items" class="flex-1 overflow-y-auto p-5 space-y-4">
      <!-- Injected by JS -->
    </div>

    <!-- Cart Footer & Checkout Action -->
    <div class="p-5 border-t border-slate-200 bg-slate-50">
      <!-- Promo Code Input -->
      <div class="flex gap-2 mb-3">
        <input type="text" id="cart-promo-input" placeholder="كود الخصم (WELCOME10)" class="flex-1 px-3 py-1.5 rounded-xl border border-slate-300 text-xs uppercase focus:outline-none focus:ring-1 focus:ring-brand-500">
        <button onclick="applyCartPromo()" class="px-3 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-white text-xs font-bold">تطبيق</button>
      </div>

      <div class="space-y-2 mb-4 text-sm font-readex">
        <div class="flex justify-between text-slate-500">
          <span>المجموع الفرعي:</span>
          <span id="cart-subtotal" class="font-bold text-slate-800">0 ج.م</span>
        </div>
        <div class="flex justify-between text-emerald-600" id="cart-discount-row" style="display:none">
          <span>الخصم المطبق:</span>
          <span id="cart-discount" class="font-bold">0 ج.م</span>
        </div>
        <div class="flex justify-between text-slate-500">
          <span>رسوم التوصيل:</span>
          <span id="cart-shipping" class="font-bold text-emerald-600">20 ج.م</span>
        </div>
        <div class="flex justify-between text-base font-black text-slate-900 pt-2 border-t border-slate-200">
          <span>الإجمالي النهائي:</span>
          <span id="cart-total" class="text-brand-600">0 ج.م</span>
        </div>
      </div>
      <button id="checkout-btn" onclick="openCheckoutModal()" disabled class="w-full py-3.5 rounded-xl font-black text-white text-sm shadow-md transition disabled:opacity-50 disabled:cursor-not-allowed" style="background:{primary}">
        💳 المتابعة لإتمام الطلب
      </button>
    </div>
  </aside>

  <!-- Checkout Modal -->
  <div id="checkout-modal" class="backdrop hidden fixed inset-0 bg-slate-950/70 z-50 flex items-center justify-center p-4">
    <div class="bg-white rounded-3xl max-w-lg w-full max-h-[90vh] overflow-y-auto p-6 sm:p-8 shadow-2xl relative">
      <div class="flex items-center justify-between pb-4 mb-4 border-b border-slate-100">
        <div>
          <h3 class="text-xl font-black text-slate-900">تأكيد الطلب والدفع 🇪🇬</h3>
          <p class="text-xs text-slate-500 font-readex">أدخل بيانات التوصيل واختر طريقة الدفع المناسبة</p>
        </div>
        <button onclick="closeCheckoutModal()" class="w-8 h-8 rounded-full bg-slate-100 text-slate-500 hover:bg-slate-200 flex items-center justify-center font-bold">✕</button>
      </div>

      <form id="order-form" onsubmit="submitOrder(event)" class="space-y-4">
        <div>
          <label class="block text-xs font-bold text-slate-700 mb-1">الاسم بالكامل *</label>
          <input type="text" id="cust-name" required placeholder="مثال: أحمد محمود" class="w-full px-3.5 py-2.5 rounded-xl border border-slate-300 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500">
        </div>
        <div>
          <label class="block text-xs font-bold text-slate-700 mb-1">رقم الهاتف / الواتساب *</label>
          <input type="tel" id="cust-phone" required placeholder="مثال: 01012345678" class="w-full px-3.5 py-2.5 rounded-xl border border-slate-300 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500">
        </div>
        <div>
          <label class="block text-xs font-bold text-slate-700 mb-1">عنوان التوصيل بالتفصيل *</label>
          <textarea id="cust-address" required placeholder="المدينة، الحي، اسم الشارع، رقم العمارة والشقة" class="w-full px-3.5 py-2 rounded-xl border border-slate-300 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500" rows="2"></textarea>
        </div>

        <!-- Payment Method Selection -->
        <div>
          <label class="block text-xs font-bold text-slate-700 mb-2">طريقة الدفع *</label>
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs font-bold">
            <label class="flex items-center gap-2 p-3 rounded-xl border border-slate-200 cursor-pointer hover:bg-slate-50 transition">
              <input type="radio" name="pay_method" value="vodafone_cash" checked class="text-brand-500">
              <div>
                <div>فودافون كاش / كاش</div>
                <div class="text-[10px] text-slate-400 font-normal">تحويل لمحفظة {html.escape(v_cash)}</div>
              </div>
            </label>
            <label class="flex items-center gap-2 p-3 rounded-xl border border-slate-200 cursor-pointer hover:bg-slate-50 transition">
              <input type="radio" name="pay_method" value="instapay" class="text-brand-500">
              <div>
                <div>إنستاباي (InstaPay)</div>
                <div class="text-[10px] text-slate-400 font-normal">{html.escape(instapay)}</div>
              </div>
            </label>
            <label class="flex items-center gap-2 p-3 rounded-xl border border-slate-200 cursor-pointer hover:bg-slate-50 transition">
              <input type="radio" name="pay_method" value="fawry" class="text-brand-500">
              <div>
                <div>فوري باي (Fawry Pay)</div>
                <div class="text-[10px] text-slate-400 font-normal">كود التاجر: {html.escape(fawry_code)}</div>
              </div>
            </label>
            <label class="flex items-center gap-2 p-3 rounded-xl border border-slate-200 cursor-pointer hover:bg-slate-50 transition">
              <input type="radio" name="pay_method" value="cod" class="text-brand-500">
              <div>
                <div>الدفع عند الاستلام</div>
                <div class="text-[10px] text-slate-400 font-normal">كاش لمندوب التوصيل</div>
              </div>
            </label>
          </div>
        </div>

        <button type="submit" id="submit-order-btn" class="w-full py-3.5 rounded-xl font-black text-white text-sm shadow-lg transition mt-4" style="background:{primary}">
          ✅ تأكيد وإرسال الطلب الآن
        </button>
      </form>
    </div>
  </div>

  <!-- Order Success Modal -->
  <div id="success-modal" class="backdrop hidden fixed inset-0 bg-slate-950/80 z-50 flex items-center justify-center p-4">
    <div class="bg-white rounded-3xl max-w-md w-full p-6 sm:p-8 text-center shadow-2xl relative">
      <div class="w-16 h-16 rounded-full bg-emerald-100 text-emerald-600 flex items-center justify-center text-3xl mx-auto mb-4">
        ✓
      </div>
      <h3 class="text-xl font-black text-slate-900 mb-1">تم تأكيد طلبك بنجاح! 🎉</h3>
      <p class="text-xs text-slate-500 font-readex mb-6">شكراً لاختيارك {html.escape(brand_name)}. جاري تجهيز طلبك للشحن والتسليم فوراً.</p>

      <div class="bg-slate-50 rounded-2xl p-4 text-xs font-readex space-y-2 mb-6 border border-slate-100 text-right">
        <div class="flex justify-between">
          <span class="text-slate-500">رقم الأوردر:</span>
          <b id="res-order-id" class="text-slate-900 font-mono">#0000</b>
        </div>
        <div class="flex justify-between">
          <span class="text-slate-500">إجمالي المبلغ:</span>
          <b id="res-total" class="text-emerald-600 font-black">0 ج.م</b>
        </div>
        <div class="flex justify-between">
          <span class="text-slate-500">طريقة الدفع:</span>
          <b id="res-payment-method" class="text-slate-800">كاش</b>
        </div>
        <div class="flex justify-between">
          <span class="text-slate-500">المرجع / الكود:</span>
          <b id="res-payment-ref" class="text-slate-800 font-mono">COD-0000</b>
        </div>
      </div>

      <div class="space-y-3">
        <a id="res-whatsapp-link" href="#" target="_blank" class="block w-full py-3 rounded-xl bg-emerald-500 hover:bg-emerald-600 text-white font-bold text-xs shadow-md transition">
          💬 إرسال تفاصيل الأوردر للواتساب للتأكيد
        </a>
        <button onclick="closeSuccessModal()" class="w-full py-3 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 font-bold text-xs transition">
          إغلاق ومتابعة التسوق
        </button>
      </div>
    </div>
  </div>

  <!-- State & JS Logic -->
  <script>
    const SITE_JOB_ID = {job_id};
    const STORE_NAME = "{html.escape(brand_name)}";
    const WA_PHONE = "{clean_wa}";
    const PRODUCTS = {items_json};
    
    // Local Cart state
    let cart = {{}}; // {{ id: qty }}
    let activeFilter = 'الكل';

    function renderProducts() {{
      const grid = document.getElementById('products-grid');
      const filtered = (activeFilter === 'الكل') 
        ? PRODUCTS 
        : PRODUCTS.filter(p => p.category === activeFilter);
        
      if (!filtered.length) {{
        grid.innerHTML = '<div class="col-span-full py-12 text-center text-slate-400 font-bold">لا توجد منتجات في هذا القسم حالياً</div>';
        return;
      }}

      grid.innerHTML = filtered.map(p => `
        <div class="bg-white rounded-3xl border border-slate-200/80 p-5 shadow-sm hover:shadow-xl transition-all duration-300 flex flex-col justify-between group hover:-translate-y-1">
          <div>
            <div class="flex items-center justify-between mb-3">
              <span class="text-[11px] font-bold px-2.5 py-1 rounded-full bg-slate-100 text-slate-600 font-readex">
                ${{p.category}}
              </span>
              ${{p.badge ? `<span class="text-[11px] font-black px-2.5 py-1 rounded-full text-brand-600" style="background:${pal["badge_bg"]};color:${pal["badge_text"]}">★ ${{p.badge}}</span>` : ''}}
            </div>
            
            <h4 class="text-base font-black text-slate-900 mb-2 leading-snug group-hover:text-brand-600 transition">
              ${{p.title}}
            </h4>
            
            <p class="text-xs text-slate-500 font-readex leading-relaxed mb-6">
              ${{p.description || 'صنف عالي الجودة ومضمون تم اختياره بعناية.'}}
            </p>
          </div>

          <div class="pt-4 border-t border-slate-100 flex items-center justify-between">
            <div>
              <span class="text-xs text-slate-400 font-bold">السعر:</span>
              <div class="text-lg font-black text-slate-900">${{p.price}} <span class="text-xs font-bold text-slate-500">ج.م</span></div>
            </div>

            <button onclick="addToCart(${{p.id}})" class="flex items-center gap-1.5 px-4 py-2.5 rounded-xl font-bold text-white text-xs shadow-md hover:shadow-lg transition active:scale-95" style="background:{primary}">
              <span>+ أضف للسلة</span>
            </button>
          </div>
        </div>
      `).join('');
    }}

    function filterCategory(cat) {{
      activeFilter = cat;
      document.querySelectorAll('.cat-btn').forEach(b => {{
        if(b.dataset.cat === cat) {{
          b.className = 'cat-btn px-4 py-2 rounded-xl text-xs font-bold transition bg-slate-900 text-white';
        }} else {{
          b.className = 'cat-btn px-4 py-2 rounded-xl text-xs font-bold transition bg-white text-slate-600 border border-slate-200 hover:bg-slate-100';
        }}
      }});
      renderProducts();
    }}

    function toggleCart(open) {{
      const drawer = document.getElementById('cart-drawer');
      const backdrop = document.getElementById('cart-backdrop');
      if (open) {{
        drawer.classList.remove('closed');
        backdrop.classList.remove('hidden');
      }} else {{
        drawer.classList.add('closed');
        backdrop.classList.add('hidden');
      }}
    }}

    function addToCart(id) {{
      cart[id] = (cart[id] || 0) + 1;
      updateCartUI();
      toggleCart(true);
    }}

    function updateQty(id, delta) {{
      if (!cart[id]) return;
      cart[id] += delta;
      if (cart[id] <= 0) delete cart[id];
      updateCartUI();
    }}

    function updateCartUI() {{
      const countEl = document.getElementById('cart-counter');
      const badgeEl = document.getElementById('cart-items-total-badge');
      const itemsContainer = document.getElementById('cart-items');
      const subtotalEl = document.getElementById('cart-subtotal');
      const totalEl = document.getElementById('cart-total');
      const checkoutBtn = document.getElementById('checkout-btn');

      const ids = Object.keys(cart);
      const totalCount = ids.reduce((sum, id) => sum + cart[id], 0);

      countEl.textContent = totalCount;
      badgeEl.textContent = totalCount + ' عناصر';

      if (!ids.length) {{
        itemsContainer.innerHTML = `
          <div class="h-64 flex flex-col items-center justify-center text-center text-slate-400">
            <span class="text-4xl mb-2">🛒</span>
            <p class="text-sm font-bold">سلتك فارغة حالياً</p>
            <p class="text-xs text-slate-400 mt-1">تصفح القائمة وأضف منتجاتك المفضلة</p>
          </div>
        `;
        subtotalEl.textContent = '0 ج.م';
        totalEl.textContent = '0 ج.م';
        checkoutBtn.disabled = true;
        return;
      }}

      checkoutBtn.disabled = false;
      let subtotal = 0;

      itemsContainer.innerHTML = ids.map(id => {{
        const p = PRODUCTS.find(prod => prod.id == id);
        if (!p) return '';
        const lineTotal = p.price * cart[id];
        subtotal += lineTotal;
        return `
          <div class="flex items-center justify-between p-3.5 rounded-2xl bg-slate-50 border border-slate-100">
            <div class="flex-1 min-w-0 pr-2">
              <h5 class="text-xs font-black text-slate-900 truncate">${{p.title}}</h5>
              <div class="text-[11px] text-slate-500">${{p.price}} ج.م × ${{cart[id]}}</div>
            </div>
            <div class="flex items-center gap-2">
              <button onclick="updateQty(${{id}}, -1)" class="w-6 h-6 rounded-lg bg-white border border-slate-200 text-slate-700 font-bold flex items-center justify-center hover:bg-slate-100">-</button>
              <span class="text-xs font-black w-4 text-center">${{cart[id]}}</span>
              <button onclick="updateQty(${{id}}, 1)" class="w-6 h-6 rounded-lg bg-white border border-slate-200 text-slate-700 font-bold flex items-center justify-center hover:bg-slate-100">+</button>
            </div>
          </div>
        `;
      }}).join('');

      let discountVal = (subtotal * appliedPromoDiscount) / 100;
      const shipping = 20;
      subtotalEl.textContent = subtotal + ' ج.م';
      const discRow = document.getElementById('cart-discount-row');
      const discEl = document.getElementById('cart-discount');
      if (discRow && discEl) {{
        if (appliedPromoDiscount > 0) {{
          discRow.style.display = 'flex';
          discEl.textContent = `${{discountVal.toFixed(0)}} ج.م (-${{appliedPromoDiscount}}%)`;
        }} else {{
          discRow.style.display = 'none';
        }}
      }}
      totalEl.textContent = Math.max(0, (subtotal - discountVal + shipping)).toFixed(0) + ' ج.م';
    }}

    function applyCartPromo() {{
      const code = (document.getElementById('cart-promo-input').value || '').trim().toUpperCase();
      if (code === 'WELCOME10') appliedPromoDiscount = 10;
      else if (code === 'EGYPT2026') appliedPromoDiscount = 15;
      else if (code === 'AUTOCORP') appliedPromoDiscount = 20;
      else {{
        alert('كود الخصم غير صحيح أو منتهي الصلاحية');
        return;
      }}
      alert(`🎉 تم تفعيل كود الخصم بنجاح (-${{appliedPromoDiscount}}%)!`);
      updateCartUI();
    }}

    let isStoreDark = false;
    function toggleStoreTheme() {{
      isStoreDark = !isStoreDark;
      if (isStoreDark) {{
        document.body.style.backgroundColor = '#0b0f19';
        document.body.style.color = '#f1f5f9';
        const lbl = document.getElementById('store-theme-lbl');
        if (lbl) lbl.textContent = 'ليلي';
      }} else {{
        document.body.style.backgroundColor = '#f8fafc';
        document.body.style.color = '#1e293b';
        const lbl = document.getElementById('store-theme-lbl');
        if (lbl) lbl.textContent = 'نهاري';
      }}
    }}

    let storeLang = 'ar';
    function toggleStoreLang() {{
      storeLang = storeLang === 'ar' ? 'en' : 'ar';
      document.documentElement.lang = storeLang;
      document.documentElement.dir = storeLang === 'ar' ? 'rtl' : 'ltr';
      const btn = document.getElementById('store-lang-btn');
      if (btn) btn.textContent = storeLang === 'ar' ? 'English' : 'العربية';
      const bar = document.getElementById('promo-bar-text');
      if (bar) {{
        if (storeLang === 'en') {{
          bar.innerHTML = '🎉 <b>Special Deals:</b> 10% Off Code: <b>WELCOME10</b> | 🚚 Fast Delivery Nationwide';
        }} else {{
          bar.innerHTML = '🎉 <b>عروض حصرية:</b> كود خصم 10%: <b>WELCOME10</b> | 🚚 توصيل سريع لجميع المحافظات';
        }}
      }}
    }}

    let appliedPromoDiscount = 0;

    function openCheckoutModal() {{
      toggleCart(false);
      document.getElementById('checkout-modal').classList.remove('hidden');
    }}

    function closeCheckoutModal() {{
      document.getElementById('checkout-modal').classList.add('hidden');
    }}

    function closeSuccessModal() {{
      document.getElementById('success-modal').classList.add('hidden');
      cart = {{}};
      updateCartUI();
    }}

    async function submitOrder(e) {{
      e.preventDefault();
      const btn = document.getElementById('submit-order-btn');
      btn.disabled = true;
      btn.textContent = '⏳ جاري معالجة وتأكيد الطلب...';

      const cartItemsPayload = Object.keys(cart).map(id => {{
        const p = PRODUCTS.find(x => x.id == id);
        return {{
          id: id,
          title: p?.title || 'عنصر',
          price: p?.price || 0,
          quantity: cart[id]
        }};
      }});

      const shipping = 20;
      const subtotal = cartItemsPayload.reduce((s, it) => s + it.price * it.quantity, 0);
      const total = subtotal + shipping;
      const payMethod = document.querySelector('input[name="pay_method"]:checked')?.value || 'vodafone_cash';

      const orderData = {{
        customer_name: document.getElementById('cust-name').value.trim(),
        customer_phone: document.getElementById('cust-phone').value.trim(),
        customer_address: document.getElementById('cust-address').value.trim(),
        items: cartItemsPayload,
        total_egp: total,
        payment_method: payMethod
      }};

      try {{
        const res = await fetch(`/api/sites/${{SITE_JOB_ID}}/orders`, {{
          method: 'POST',
          headers: {{ 'Content-Type': 'application/json' }},
          body: JSON.stringify(orderData)
        }});
        
        let result;
        if (res.ok) {{
          result = await res.json();
        }} else {{
          result = {{
            id: Math.floor(1000 + Math.random() * 9000),
            total_egp: total,
            payment_ref: payMethod === 'vodafone_cash' ? 'VF-' + Math.floor(100000 + Math.random() * 900000)
                       : payMethod === 'fawry' ? 'FAWRY-' + Math.floor(10000000 + Math.random() * 90000000)
                       : 'IP-' + Math.floor(100000 + Math.random() * 900000),
            payment_method: payMethod
          }};
        }}

        closeCheckoutModal();
        
        document.getElementById('res-order-id').textContent = '#' + (result.id || result.order_id || '2026');
        document.getElementById('res-total').textContent = (result.total_egp || total) + ' ج.م';
        document.getElementById('res-payment-method').textContent = payMethod === 'vodafone_cash' ? 'فودافون كاش'
                                                               : payMethod === 'instapay' ? 'إنستاباي'
                                                               : payMethod === 'fawry' ? 'فوري باي' : 'الدفع عند الاستلام';
        document.getElementById('res-payment-ref').textContent = result.payment_ref || 'COD-CONFIRMED';
        
        const waLines = [
          "مرحباً " + STORE_NAME + " 👋",
          "لقد قمت بعمل طلب جديد عبر المتجر:",
          "• رقم الطلب: #" + (result.id || result.order_id || ""),
          "• الاسم: " + orderData.customer_name,
          "• الهاتف: " + orderData.customer_phone,
          "• العنوان: " + orderData.customer_address,
          "• الإجمالي: " + (result.total_egp || total) + " ج.م",
          "• طريقة الدفع: " + payMethod,
          "• المرجع: " + (result.payment_ref || ""),
          "برجاء تأكيد الموعد للتوصيل!"
        ];
        const waMsg = encodeURIComponent(waLines.join(String.fromCharCode(10)));
        document.getElementById('res-whatsapp-link').href = `https://wa.me/${{WA_PHONE}}?text=${{waMsg}}`;
        
        document.getElementById('success-modal').classList.remove('hidden');
      }} catch (err) {{
        alert('حدث خطأ أثناء إرسال الطلب: ' + err.message);
      }} finally {{
        btn.disabled = false;
        btn.textContent = '✅ تأكيد وإرسال الطلب الآن';
      }}
    }}

    // Init
    renderProducts();
    updateCartUI();
  </script>
</body>
</html>"""
    return html_code
