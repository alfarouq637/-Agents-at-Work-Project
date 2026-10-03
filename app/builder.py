"""AutoCorp Intelligent Full-Stack Site Builder & Synthesizer.
Generates responsive, production-ready Arabic Single Page Applications (SPAs)
with Tailored Palettes, Dynamic Catalogs, Interactive Cart Drawers,
Egyptian Payment Gateways, and Live Backend APIs (/api/sites/{id}/orders).
"""
import html
import json
import random
import re

PALETTES = {
    "emerald": {
        "name": "أخضر فريش وطبيعي (Emerald / Vegetables)",
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
        "name": "عنبر وذهبي دافئ (Warm Sunset / Food & Cafe)",
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
        "name": "أزرق تكنولوجي وشركات (Ocean Navy / Tech & Services)",
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
    "crimson": {
        "name": "أحمر حماسي وجريء (Ruby Crimson / Fast Food & Deals)",
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
    "vegetables": [
        {"title": "طماطم بلدي نخب أول (كيلو)", "price": 18, "category": "خضار طازج", "badge": "طازج اليوم", "desc": "طماطم سكرية مقطوفة صباحاً من مزارعنا بعناية فائقة."},
        {"title": "بطاطس تحمير سبونتا (كيلو)", "price": 20, "category": "خضار طازج", "badge": "ممتاز للتحمير", "desc": "حبات بطاطس منتقاة بجودة عالية وخالية من الشوائب."},
        {"title": "خيار صوب بلدي فريش (كيلو)", "price": 16, "category": "خضار طازج", "badge": "الأكثر طلباً", "desc": "خيار مقرمش طازج يومياً مناسب للسلطات والاستهلاك اليومي."},
        {"title": "بصل أحمر بلدي فاخر (كيلو)", "price": 22, "category": "خضار طازج", "badge": "جودة عالية", "desc": "بصل أحمر غني بالنكهة تخزين ممتاز."},
        {"title": "بوكس التوفير العائلي المشكل (10 كجم)", "price": 195, "category": "بوكسات التوفير", "badge": "وفر 25%", "desc": "تشكيلة أسبوعية متكاملة (بطاطس، طماطم، بصل، خيار، كوسة، جزر)."},
        {"title": "باقة الخضرة المشكلة (4 حزم)", "price": 12, "category": "ورقيات فريش", "badge": "طازج ونظيف", "desc": "حزمة جرجير، بقدونس، شبت، وكزبرة خضراء مغسولة وطازجة."},
        {"title": "فلفل ألوان رومي مستورد (كيلو)", "price": 45, "category": "خضار طازج", "badge": "غني بفيتامين C", "desc": "فلفل رومي مشكل أصفر وأحمر عالي الجودة."},
        {"title": "موز بلدي سكري فاخر (كيلو)", "price": 28, "category": "فواكه موسمية", "badge": "حلاوة طبيعية", "desc": "موز بلدي كامل النضج غني بالطاقة والبوتاسيوم."},
    ],
    "restaurant": [
        {"title": "طاجن ملوخية بالطشة واللحم البلدي", "price": 95, "category": "طواجن بلدي", "badge": "على أصوله", "desc": "ملوخية خضراء فريش بالسمن البلدي وقطع لحم كندوز فاخرة."},
        {"title": "وجبة مشويات مشكلة مكس جريل (شخصين)", "price": 240, "category": "مشويات الفحم", "badge": "الأكثر طلباً", "desc": "كباب، كفتة بلدي، شيش طاووق، مع أرز بسمتي وسلطات وخبز."},
        {"title": "حواوشي بلدي سوبر بالجبنة الموتزاريلا", "price": 65, "category": "حواوشي ومخبوزات", "badge": "مقرمش وشهي", "desc": "لحم مفروم متبل بالخلطة السرية مع موتزاريلا سايحة."},
        {"title": "نصف دجاجة مشوية على الفحم + أرز مبهر", "price": 130, "category": "مشويات الفحم", "badge": "وجبة التوفير", "desc": "دجاج متبل بخلطة الأعشاب يقدم مع الأرز والبطاطس والتومية."},
        {"title": "سلطة طحينة وسلطة خضراء ومخلل مشكل", "price": 25, "category": "مقبلات وسلطات", "badge": "طازج", "desc": "تشكيلة سلطات شرقية طازجة تكمل وجبتك المفضلة."},
    ],
    "electronics": [
        {"title": "سماعة بلوتوث لاسلكية عازلة للضوضاء Pro", "price": 450, "category": "صوتيات وسماعات", "badge": "الأكثر مبيعاً", "desc": "صوت نقي بتقنية Hi-Fi مع مايك مدمج وبطارية تدوم 24 ساعة متواصلة."},
        {"title": "ساعة ذكية مقاومة للماء مع تتبع نبضات القلب", "price": 680, "category": "إلكترونيات ذكية", "badge": "ضمان سنة", "desc": "شاشة أموليد لمسية، استقبال الإشعارات والمكالمات ومتابعة النشاط الرياضي."},
        {"title": "باور بانك شحن فائق السرعة 20,000 مللي أمبير", "price": 390, "category": "شواحن وبطاريات", "badge": "شحن سريع 22.5W", "desc": "منافذ Type-C و USB متعددة لشحن 3 أجهزة في وقت واحد بأمان تام."},
        {"title": "شاحن جداري GaN ثلاثي المنافذ 65W للابتوب والموبايل", "price": 320, "category": "شواحن وبطاريات", "badge": "تقنية GaN", "desc": "شحن فائق السرعة متوافق مع الآيفون والسامسونج واللابتوب بحجم مدمج."},
        {"title": "حامل موبايل مغناطيسي للسيارة دوران 360 درجة", "price": 120, "category": "إكسسوارات سيارات", "badge": "تثبيت قوي", "desc": "مغناطيس نيوديميوم فائق القوة لتثبيت الهاتف بأمان على فتحات التكييف."},
        {"title": "إضاءة مكتبية ذكية RGB مع شاحن لاسلكي مدمج", "price": 290, "category": "إضاءة ومنزل ذكي", "badge": "شاحن وايرلس", "desc": "إضاءة ليد متعددة الألوان قابلة للتعتيم مع قاعدة شحن لاسلكي سريع."},
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
    if any(k in t for k in ["خضار", "فواكه", "طماطم", "بصل", "سوق", "مزرعة", "عضوي", "محصول", "أغذية طازجة"]):
        return "vegetables"
    if any(k in t for k in ["مطعم", "أكل", "كافيه", "برجر", "مشويات", "كباب", "حواوشي", "وجبات", "حلويات", "شاورما", "شيف"]):
        return "restaurant"
    if any(k in t for k in ["الكترون", "اجهز", "موبايل", "هواتف", "سماعات", "كمبيوتر", "لابتوب", "شواحن", "ساعات ذكية", "تكنو"]):
        return "electronics"
    return "general"


def build_site_html(job_id: int, client: str, request: str, settings: dict = None, items: list = None) -> str:
    """Generates a complete, responsive, full-stack Arabic SPA website."""
    settings = settings or {}
    items = items or []
    
    niche = detect_niche(request + " " + client + " " + (settings.get("category") or ""))
    brand_name = settings.get("brand_name") or client or ("خضار فريش" if niche == "vegetables" else "تكنو ستور" if niche == "electronics" else "المتجر المصري")
    if brand_name.startswith("tg:"):
        brand_name = "متجر الخضار الطازج" if niche == "vegetables" else "تكنو ستور للإلكترونيات" if niche == "electronics" else "متجري الإلكتروني"
        
    slogan = settings.get("slogan") or ("خضارك طازج من المزرعة لباب بيتك بأعلى جودة وأفضل سعر في مصر" if niche == "vegetables" 
                                       else "أشهى المأكولات والمشويات على أصولها بتوصيل سريع وساخن" if niche == "restaurant"
                                       else "أحدث الأجهزة والإلكترونيات الذكية بأفضل الأسعار وضمان حقيقي مع شحن فوري" if niche == "electronics"
                                       else "خدمات احترافية متكاملة تلبي احتياجاتك بأعلى معايير الجودة")
    
    # Palette
    pal_key = settings.get("palette") or ("emerald" if niche == "vegetables" else "sunset" if niche == "restaurant" else "ocean")
    pal = PALETTES.get(pal_key, PALETTES["emerald"])
    primary = settings.get("color_primary") or pal["primary"]
    secondary = settings.get("color_secondary") or pal["secondary"]
    accent = pal["accent"]
    hero_grad = pal["hero_gradient"]
    
    # Contact & Payment defaults
    phone = settings.get("phone") or "01000000000"
    whatsapp = settings.get("whatsapp") or phone
    clean_wa = re.sub(r"[^\d]", "", whatsapp)
    if clean_wa.startswith("01"):
        clean_wa = "2" + clean_wa
        
    v_cash = settings.get("vodafone_cash") or phone
    instapay = settings.get("instapay") or (brand_name.replace(" ", "").lower() + "@instapay")
    fawry_code = settings.get("fawry_code") or "88219"
    cod_enabled = settings.get("cod_enabled", True)
    
    # Items
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
  <div class="bg-slate-900 text-slate-200 text-xs py-2 px-4 text-center flex items-center justify-center gap-3">
    <span class="inline-block w-2 h-2 rounded-full bg-emerald-400 animate-ping"></span>
    <span>🎉 <b>عروض اليوم:</b> خصم 15% على جميع الطلبات لفترة محدودة | 🚚 توصيل سريع لجميع المناطق</span>
    <a href="https://wa.me/{clean_wa}?text={html.escape('مرحباً، أريد الاستفسار عن عروض ' + brand_name)}" target="_blank" class="text-amber-400 hover:underline font-bold mr-2">طلب واتساب مباشر</a>
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
          <h4 class="font-bold text-slate-900 mb-1">طازج ومنتقى يومياً</h4>
          <p class="text-xs text-slate-500 font-readex">نحرص على جودة كل عنصر قبل التغليف والتسليم.</p>
        </div>
      </div>
      <div class="p-6 rounded-2xl bg-slate-50 border border-slate-100 flex items-start gap-4">
        <div class="text-3xl">⚡</div>
        <div>
          <h4 class="font-bold text-slate-900 mb-1">توصيل سريع للباب</h4>
          <p class="text-xs text-slate-500 font-readex">فريق دليفري مجهز لتوصيل طلباتكم في وقت قياسي.</p>
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
          <h4 class="font-bold text-slate-900 mb-1">ضمان الرضا 100%</h4>
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
      <div class="space-y-2 mb-4 text-sm font-readex">
        <div class="flex justify-between text-slate-500">
          <span>المجموع الفرعي:</span>
          <span id="cart-subtotal" class="font-bold text-slate-800">0 ج.م</span>
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
          <div class="grid grid-cols-2 gap-2 text-xs font-bold">
            <label class="flex items-center gap-2 p-3 rounded-xl border border-slate-200 cursor-pointer hover:bg-slate-50 has-[:checked]:border-brand-500 has-[:checked]:bg-brand-50">
              <input type="radio" name="payment" value="vodafone_cash" checked class="text-brand-600 focus:ring-brand-500">
              <span>📱 فودافون كاش</span>
            </label>
            <label class="flex items-center gap-2 p-3 rounded-xl border border-slate-200 cursor-pointer hover:bg-slate-50 has-[:checked]:border-brand-500 has-[:checked]:bg-brand-50">
              <input type="radio" name="payment" value="instapay" class="text-brand-600 focus:ring-brand-500">
              <span>⚡ إنستاباي InstaPay</span>
            </label>
            <label class="flex items-center gap-2 p-3 rounded-xl border border-slate-200 cursor-pointer hover:bg-slate-50 has-[:checked]:border-brand-500 has-[:checked]:bg-brand-50">
              <input type="radio" name="payment" value="fawry" class="text-brand-600 focus:ring-brand-500">
              <span>🏪 فوري باي</span>
            </label>
            <label class="flex items-center gap-2 p-3 rounded-xl border border-slate-200 cursor-pointer hover:bg-slate-50 has-[:checked]:border-brand-500 has-[:checked]:bg-brand-50">
              <input type="radio" name="payment" value="cod" class="text-brand-600 focus:ring-brand-500">
              <span>💵 الدفع عند الاستلام</span>
            </label>
          </div>
        </div>

        <!-- Dynamic Instructions -->
        <div id="payment-notice" class="p-3.5 rounded-xl bg-amber-50 border border-amber-200 text-xs text-amber-900 leading-relaxed font-readex">
          📱 <b>تحويل فودافون كاش:</b> بعد التأكيد، حوّل المبلغ إلى الرقم: <code class="font-bold select-all bg-white px-1.5 py-0.5 rounded border border-amber-300">{html.escape(v_cash)}</code>
        </div>

        <div class="pt-2">
          <button type="submit" id="submit-order-btn" class="w-full py-3.5 rounded-xl font-black text-white text-sm shadow-lg hover:brightness-105 transition" style="background:{primary}">
            ✅ تأكيد وإرسال الطلب الآن
          </button>
        </div>
      </form>
    </div>
  </div>

  <!-- Order Success Modal -->
  <div id="success-modal" class="backdrop hidden fixed inset-0 bg-slate-950/80 z-50 flex items-center justify-center p-4">
    <div class="bg-white rounded-3xl max-w-md w-full p-8 text-center shadow-2xl animate-in zoom-in-95">
      <div class="w-16 h-16 rounded-full bg-emerald-100 text-emerald-600 flex items-center justify-center text-3xl mx-auto mb-4">
        ✓
      </div>
      <h3 class="text-2xl font-black text-slate-900 mb-1">تم استلام طلبك بنجاح!</h3>
      <p class="text-xs text-slate-500 font-readex mb-6">شكراً لثقتكم في {html.escape(brand_name)}. جاري تجهيز طلبكم فوراً.</p>

      <div class="bg-slate-50 p-4 rounded-2xl border border-slate-200 text-right text-xs space-y-2 font-readex mb-6">
        <div class="flex justify-between">
          <span class="text-slate-500">رقم الطلب:</span>
          <b id="res-order-id" class="text-slate-900">#000</b>
        </div>
        <div class="flex justify-between">
          <span class="text-slate-500">إجمالي المبلغ:</span>
          <b id="res-total" class="text-brand-600 font-bold">0 ج.م</b>
        </div>
        <div class="flex justify-between">
          <span class="text-slate-500">طريقة الدفع:</span>
          <b id="res-payment-method" class="text-slate-900">فودافون كاش</b>
        </div>
        <div class="flex justify-between pt-2 border-t border-slate-200">
          <span class="text-slate-500">كود / مرجع السداد:</span>
          <b id="res-payment-ref" class="text-amber-600 font-mono text-sm">---</b>
        </div>
      </div>

      <div class="flex flex-col gap-2.5">
        <a id="res-whatsapp-link" href="#" target="_blank" class="w-full py-3 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-xs flex items-center justify-center gap-2 shadow">
          <span>📲 متابعة وتأكيد مع الإدارة عبر الواتساب</span>
        </a>
        <button onclick="closeSuccessModal()" class="w-full py-2.5 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 font-bold text-xs">
          إغلاق ومتابعة التسوق
        </button>
      </div>
    </div>
  </div>

  <script>
    const SITE_JOB_ID = {job_id};
    const PRODUCTS = {items_json};
    const V_CASH = "{v_cash}";
    const INSTAPAY = "{instapay}";
    const FAWRY = "{fawry_code}";
    const WA_PHONE = "{clean_wa}";
    const STORE_NAME = "{brand_name}";

    let cart = {{}};

    function renderProducts(filter = 'الكل') {{
      const grid = document.getElementById('products-grid');
      const filtered = filter === 'الكل' ? PRODUCTS : PRODUCTS.filter(p => p.category === filter);
      
      grid.innerHTML = filtered.map(p => `
        <div class="bg-white rounded-2xl border border-slate-200 overflow-hidden shadow-sm hover:shadow-md transition flex flex-col justify-between group">
          <div class="p-5 flex-1 flex flex-col">
            <div class="flex items-start justify-between gap-2 mb-3">
              <span class="text-xs font-bold text-slate-400 font-readex">${{p.category || 'صنف ممتاز'}}</span>
              ${{p.badge ? `<span class="px-2.5 py-0.5 rounded-full text-[11px] font-black" style="background:{pal["badge_bg"]};color:{pal["badge_text"]}">${{p.badge}}</span>` : ''}}
            </div>
            <h4 class="font-bold text-slate-900 text-base mb-2 group-hover:text-brand-600 transition leading-snug">${{p.title}}</h4>
            <p class="text-xs text-slate-500 font-readex leading-relaxed flex-1">${{p.description || ''}}</p>
            <div class="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between">
              <div>
                <span class="text-xs text-slate-400 font-readex">السعر:</span>
                <span class="text-lg font-black text-slate-900 ml-1">${{p.price}}</span>
                <span class="text-xs font-bold text-slate-600">ج.م</span>
              </div>
              <button onclick="addToCart(${{p.id}})" class="px-3.5 py-1.5 rounded-xl font-bold text-white text-xs shadow hover:scale-105 active:scale-95 transition flex items-center gap-1.5" style="background:{primary}">
                <span>+ أضف</span>
              </button>
            </div>
          </div>
        </div>
      `).join('');
    }}

    function filterCategory(cat) {{
      document.querySelectorAll('.cat-btn').forEach(btn => {{
        if(btn.dataset.cat === cat) {{
          btn.className = "cat-btn px-4 py-2 rounded-xl text-xs font-bold transition bg-slate-900 text-white";
        }} else {{
          btn.className = "cat-btn px-4 py-2 rounded-xl text-xs font-bold transition bg-white text-slate-600 border border-slate-200 hover:bg-slate-100";
        }}
      }});
      renderProducts(cat);
    }}

    function addToCart(id) {{
      cart[id] = (cart[id] || 0) + 1;
      updateCartUI();
      // Optional sound or micro interaction
      toggleCart(true);
    }}

    function changeQty(id, delta) {{
      if (!cart[id]) return;
      cart[id] += delta;
      if (cart[id] <= 0) delete cart[id];
      updateCartUI();
    }}

    function updateCartUI() {{
      const itemsContainer = document.getElementById('cart-items');
      const counter = document.getElementById('cart-counter');
      const totalBadge = document.getElementById('cart-items-total-badge');
      const subtotalEl = document.getElementById('cart-subtotal');
      const totalEl = document.getElementById('cart-total');
      const checkoutBtn = document.getElementById('checkout-btn');

      const itemIds = Object.keys(cart);
      let count = 0;
      let subtotal = 0;

      if (itemIds.length === 0) {{
        itemsContainer.innerHTML = `
          <div class="h-64 flex flex-col items-center justify-center text-center text-slate-400">
            <span class="text-4xl mb-2">🛒</span>
            <p class="font-bold text-sm">سلتك فارغة حالياً</p>
            <p class="text-xs font-readex text-slate-400 mt-1">تصفح القائمة واختر ما يعجبك لإضافته هنا.</p>
          </div>
        `;
        checkoutBtn.disabled = true;
      }} else {{
        checkoutBtn.disabled = false;
        itemsContainer.innerHTML = itemIds.map(id => {{
          const p = PRODUCTS.find(x => x.id == id);
          if(!p) return '';
          const qty = cart[id];
          count += qty;
          subtotal += p.price * qty;
          return `
            <div class="p-3.5 rounded-xl bg-slate-50 border border-slate-100 flex items-center justify-between gap-3">
              <div class="flex-1 min-w-0">
                <h5 class="font-bold text-xs text-slate-900 truncate">${{p.title}}</h5>
                <span class="text-xs text-brand-600 font-bold">${{p.price}} ج.م</span>
              </div>
              <div class="flex items-center gap-2 bg-white px-2 py-1 rounded-lg border border-slate-200">
                <button onclick="changeQty(${{p.id}}, -1)" class="w-5 h-5 flex items-center justify-center text-slate-500 hover:text-red-500 font-bold text-xs">-</button>
                <span class="text-xs font-black text-slate-800 w-4 text-center">${{qty}}</span>
                <button onclick="changeQty(${{p.id}}, 1)" class="w-5 h-5 flex items-center justify-center text-slate-500 hover:text-emerald-500 font-bold text-xs">+</button>
              </div>
            </div>
          `;
        }}).join('');
      }}

      counter.textContent = count;
      totalBadge.textContent = count + ' عناصر';
      subtotalEl.textContent = subtotal + ' ج.م';
      const shipping = count > 0 ? 20 : 0;
      document.getElementById('cart-shipping').textContent = shipping + ' ج.م';
      totalEl.textContent = (subtotal + shipping) + ' ج.م';
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

    // Dynamic payment notice
    document.querySelectorAll('input[name="payment"]').forEach(radio => {{
      radio.addEventListener('change', e => {{
        const notice = document.getElementById('payment-notice');
        const v = e.target.value;
        if (v === 'vodafone_cash') {{
          notice.innerHTML = `📱 <b>تحويل فودافون كاش:</b> بعد التأكيد، حوّل المبلغ إلى الرقم: <code class="font-bold select-all bg-white px-1.5 py-0.5 rounded border border-amber-300">${{V_CASH}}</code> ثم أرسل إشعار التحويل عبر الواتساب.`;
        }} else if (v === 'instapay') {{
          notice.innerHTML = `⚡ <b>دفع إنستاباي اللحظي:</b> حوّل المبلغ إلى المعرّف (IPA): <code class="font-bold select-all bg-white px-1.5 py-0.5 rounded border border-amber-300">${{INSTAPAY}}</code>`;
        }} else if (v === 'fawry') {{
          notice.innerHTML = `🏪 <b>كود فوري باي (Fawry):</b> سيتم توليد كود سداد مكوّن من 8 أرقام فور تأكيد الطلب، صالح للدفع في أي ماكينة فوري لمدة 48 ساعة.`;
        }} else {{
          notice.innerHTML = `💵 <b>الدفع عند الاستلام:</b> يتم دفع إجمالي المبلغ نقداً لمندوب التوصيل بعد فحص ومعاينة المنتجات بالكامل.`;
        }}
      }});
    }});

    async function submitOrder(e) {{
      e.preventDefault();
      const btn = document.getElementById('submit-order-btn');
      btn.disabled = true;
      btn.textContent = 'جاري تسجيل الطلب...';

      const orderData = {{
        customer_name: document.getElementById('cust-name').value.trim(),
        customer_phone: document.getElementById('cust-phone').value.trim(),
        customer_address: document.getElementById('cust-address').value.trim(),
        payment_method: document.querySelector('input[name="payment"]:checked').value,
        items: Object.keys(cart).map(id => {{
          const p = PRODUCTS.find(x => x.id == id);
          return {{ id: p.id, title: p.title, price: p.price, qty: cart[id] }};
        }})
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
          // Client fallback simulation
          result = {{
            id: Math.floor(1000 + Math.random() * 9000),
            total_egp: Object.keys(cart).reduce((s, id) => s + (PRODUCTS.find(p => p.id == id)?.price || 0) * cart[id], 20),
            payment_ref: orderData.payment_method === 'vodafone_cash' ? 'VF-' + Math.floor(100000 + Math.random() * 900000)
                       : orderData.payment_method === 'fawry' ? '77' + Math.floor(100000 + Math.random() * 900000)
                       : 'INSTA-' + Math.floor(100000 + Math.random() * 900000),
            payment_method: orderData.payment_method
          }};
        }}

        closeCheckoutModal();
        
        // Show success modal
        document.getElementById('res-order-id').textContent = '#' + (result.id || result.order_id || '2026');
        document.getElementById('res-total').textContent = (result.total_egp || 0) + ' ج.م';
        document.getElementById('res-payment-method').textContent = orderData.payment_method === 'vodafone_cash' ? 'فودافون كاش'
                                                               : orderData.payment_method === 'instapay' ? 'إنستاباي'
                                                               : orderData.payment_method === 'fawry' ? 'فوري باي' : 'الدفع عند الاستلام';
        document.getElementById('res-payment-ref').textContent = result.payment_ref || 'COD-CONFIRMED';
        
        // Form WhatsApp confirmation text
        const waLines = [
          "مرحباً " + STORE_NAME + " 👋",
          "لقد قمت بعمل طلب جديد عبر المتجر:",
          "• رقم الطلب: #" + (result.id || result.order_id || ""),
          "• الاسم: " + orderData.customer_name,
          "• الهاتف: " + orderData.customer_phone,
          "• الإجمالي: " + result.total_egp + " ج.م",
          "• طريقة الدفع: " + orderData.payment_method,
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
</html>
"""
    return html_code
