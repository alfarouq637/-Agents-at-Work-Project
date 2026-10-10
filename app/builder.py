"""AutoCorp Intelligent Full-Stack Site Builder & Synthesizer.
Generates responsive, production-ready Arabic & English Single Page Applications (SPAs)
with Tailored Palettes, Dynamic Catalogs, Interactive Cart Drawers,
Egyptian Payment Gateways, and Live Backend APIs (/api/sites/{id}/orders).

Supported Archetypes:
- Portfolios & CVs (Cybersecurity, Software Engineering, Design, Consulting)
- Automotive & Electric Vehicles (EV Showrooms, Chargers, Battery Health)
- Perfumes & Fragrances (Luxury Ouds, French Perfumes, Natural Oils)
- Modern Furniture & Decor (Living Rooms, Ergonomic Desks, Bed Sets)
- Books & Literature (Bestsellers, AI/Tech Blueprint, Cultural Compendiums)
- Gym, Sports & Supplements (Whey Isolate, Creatine, Weights & Gear)
- Pets & Animal Supplies (Super Premium Dry Food, Care & Scratchers)
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
import math
import random
import re

from . import artifacts


def _json_for_script(value) -> str:
    """Serialize tenant data without allowing it to close an inline script tag."""
    return (
        json.dumps(value, ensure_ascii=False)
        .replace("<", "\\u003c")
        .replace(">", "\\u003e")
        .replace("&", "\\u0026")
        .replace("\u2028", "\\u2028")
        .replace("\u2029", "\\u2029")
    )


def _inline_js_value(value) -> str:
    """Encode a value for JavaScript source inside an HTML event attribute."""
    return html.escape(_json_for_script(str(value)), quote=True)


def _safe_price(value) -> float:
    """Keep generated markup from treating a stored catalog value as code."""
    try:
        price = float(value)
    except (TypeError, ValueError):
        return 0.0
    return price if math.isfinite(price) and price >= 0 else 0.0


def _safe_text(value, fallback: str, max_length: int = 240) -> str:
    """Normalize merchant text before it reaches an HTML template."""
    text = str(value or "").strip()
    return text[:max_length] if text else fallback


def _safe_hex_color(value, fallback: str) -> str:
    """Allow only CSS hex colors in style and Tailwind configuration slots."""
    candidate = str(value or "").strip()
    return candidate if re.fullmatch(r"#[0-9A-Fa-f]{3}(?:[0-9A-Fa-f]{3})?(?:[0-9A-Fa-f]{2})?", candidate) else fallback


def _safe_phone(value, fallback: str = "") -> str:
    """Keep telephone URLs and displayed contact values free of markup."""
    digits = re.sub(r"\D", "", str(value or ""))[:20]
    return digits or fallback



PALETTES = {
    "cyber": {
        "name": "أمن سيبراني وهاكرز تيك (Calm Obsidian / Neon Cyan & Emerald)",
        "primary": "#00f2fe",
        "primary_dark": "#0891b2",
        "secondary": "#00f5a0",
        "accent": "#ffb800",
        "neon_accent": "#00f2fe",
        "neon_glow": "rgba(0, 242, 254, 0.25)",
        "bg_light": "#0b0f17",
        "hero_gradient": "linear-gradient(135deg, #020617 0%, #0b0f17 50%, #1e293b 100%)",
        "badge_bg": "rgba(0, 242, 254, 0.15)",
        "badge_text": "#00f2fe",
    },
    "automotive": {
        "name": "سيارات كهربائية وأوتو (Calm Obsidian / Electric Cyan & Cobalt)",
        "primary": "#0284c7",
        "primary_dark": "#0369a1",
        "secondary": "#06b6d4",
        "accent": "#10b981",
        "neon_accent": "#38bdf8",
        "neon_glow": "rgba(2, 132, 199, 0.25)",
        "bg_light": "#08101e",
        "hero_gradient": "linear-gradient(135deg, #020617 0%, #0c1a30 50%, #1e293b 100%)",
        "badge_bg": "rgba(2, 132, 199, 0.15)",
        "badge_text": "#38bdf8",
    },
    "perfumes": {
        "name": "عطور شرقية وفاخرة (Calm Night / Neon Amethyst & Rose)",
        "primary": "#a855f7",
        "primary_dark": "#9333ea",
        "secondary": "#ec4899",
        "accent": "#fbbf24",
        "neon_accent": "#c084fc",
        "neon_glow": "rgba(168, 85, 247, 0.25)",
        "bg_light": "#150820",
        "hero_gradient": "linear-gradient(135deg, #10031c 0%, #220b38 50%, #30104f 100%)",
        "badge_bg": "rgba(168, 85, 247, 0.15)",
        "badge_text": "#c084fc",
    },
    "furniture": {
        "name": "أثاث وديكور راقي (Calm Charcoal / Warm Bronze & Amber)",
        "primary": "#d97706",
        "primary_dark": "#b45309",
        "secondary": "#059669",
        "accent": "#f59e0b",
        "neon_accent": "#fbbf24",
        "neon_glow": "rgba(217, 119, 6, 0.25)",
        "bg_light": "#191208",
        "hero_gradient": "linear-gradient(135deg, #140d06 0%, #26180a 50%, #3b2510 100%)",
        "badge_bg": "rgba(217, 119, 6, 0.15)",
        "badge_text": "#fbbf24",
    },
    "books": {
        "name": "مكتبة وكتب (Calm Ink / Neon Emerald & Teal)",
        "primary": "#0d9488",
        "primary_dark": "#0f766e",
        "secondary": "#0284c7",
        "accent": "#f59e0b",
        "neon_accent": "#2dd4bf",
        "neon_glow": "rgba(13, 148, 136, 0.25)",
        "bg_light": "#061313",
        "hero_gradient": "linear-gradient(135deg, #040d0d 0%, #0a1e1e 50%, #112d2d 100%)",
        "badge_bg": "rgba(13, 148, 136, 0.15)",
        "badge_text": "#2dd4bf",
    },
    "gym": {
        "name": "رياضة ولياقة بدنية (Calm Carbon / Neon Orange & Ruby)",
        "primary": "#ea580c",
        "primary_dark": "#c2410c",
        "secondary": "#e11d48",
        "accent": "#fbbf24",
        "neon_accent": "#f97316",
        "neon_glow": "rgba(234, 88, 12, 0.25)",
        "bg_light": "#170a04",
        "hero_gradient": "linear-gradient(135deg, #0f0502 0%, #240d05 50%, #381508 100%)",
        "badge_bg": "rgba(234, 88, 12, 0.15)",
        "badge_text": "#f97316",
    },
    "pets": {
        "name": "حيوانات أليفة (Calm Slate / Neon Mint & Coral)",
        "primary": "#14b8a6",
        "primary_dark": "#0d9488",
        "secondary": "#f59e0b",
        "accent": "#06b6d4",
        "neon_accent": "#2dd4bf",
        "neon_glow": "rgba(20, 184, 166, 0.25)",
        "bg_light": "#061514",
        "hero_gradient": "linear-gradient(135deg, #030d0d 0%, #09201f 50%, #103230 100%)",
        "badge_bg": "rgba(20, 184, 166, 0.15)",
        "badge_text": "#2dd4bf",
    },
    "amber": {
        "name": "عسلي وذهبي نيون هادئ (Calm Slate / Neon Amber & Gold)",
        "primary": "#ffb800",
        "primary_dark": "#d97706",
        "secondary": "#00f5a0",
        "accent": "#ff7a00",
        "neon_accent": "#ffb800",
        "neon_glow": "rgba(255, 184, 0, 0.25)",
        "bg_light": "#0f172a",
        "hero_gradient": "linear-gradient(135deg, #1e1b18 0%, #171d2b 50%, #292524 100%)",
        "badge_bg": "rgba(255, 184, 0, 0.15)",
        "badge_text": "#ffb800",
    },
    "emerald": {
        "name": "أخضر نيون نقي وفريش (Calm Charcoal / Neon Mint Emerald)",
        "primary": "#00f5a0",
        "primary_dark": "#059669",
        "secondary": "#00f2fe",
        "accent": "#ffb800",
        "neon_accent": "#00f5a0",
        "neon_glow": "rgba(0, 245, 160, 0.25)",
        "bg_light": "#081210",
        "hero_gradient": "linear-gradient(135deg, #051410 0%, #081a14 50%, #102a20 100%)",
        "badge_bg": "rgba(0, 245, 160, 0.15)",
        "badge_text": "#00f5a0",
    },
    "sunset": {
        "name": "عنبر نيون دافئ (Calm Dark / Neon Tangerine Glow)",
        "primary": "#ff7a00",
        "primary_dark": "#ea580c",
        "secondary": "#ff3366",
        "accent": "#ffb800",
        "neon_accent": "#ff7a00",
        "neon_glow": "rgba(255, 122, 0, 0.25)",
        "bg_light": "#120d09",
        "hero_gradient": "linear-gradient(135deg, #1a0f07 0%, #120d09 50%, #24140a 100%)",
        "badge_bg": "rgba(255, 122, 0, 0.15)",
        "badge_text": "#ff7a00",
    },
    "ocean": {
        "name": "أزرق تكنولوجي نيون (Calm Midnight / Neon Electric Blue)",
        "primary": "#00d2ff",
        "primary_dark": "#0284c7",
        "secondary": "#00f5d4",
        "accent": "#00f5a0",
        "neon_accent": "#00d2ff",
        "neon_glow": "rgba(0, 210, 255, 0.25)",
        "bg_light": "#08101e",
        "hero_gradient": "linear-gradient(135deg, #040812 0%, #08101e 50%, #0e1c34 100%)",
        "badge_bg": "rgba(0, 210, 255, 0.15)",
        "badge_text": "#00d2ff",
    },
    "royal": {
        "name": "بنفسجي ملكي نيون (Calm Deep Dark / Neon Violet Glow)",
        "primary": "#a855f7",
        "primary_dark": "#7c3aed",
        "secondary": "#ec4899",
        "accent": "#00f2fe",
        "neon_accent": "#a855f7",
        "neon_glow": "rgba(168, 85, 247, 0.25)",
        "bg_light": "#0f0c1b",
        "hero_gradient": "linear-gradient(135deg, #090712 0%, #0f0c1b 50%, #1a1430 100%)",
        "badge_bg": "rgba(168, 85, 247, 0.15)",
        "badge_text": "#a855f7",
    },
    "teal": {
        "name": "فيروزي طبي نيون هادئ (Calm Deep Teal / Neon Turquoise)",
        "primary": "#2dd4bf",
        "primary_dark": "#0d9488",
        "secondary": "#38bdf8",
        "accent": "#00f5a0",
        "neon_accent": "#2dd4bf",
        "neon_glow": "rgba(45, 212, 191, 0.25)",
        "bg_light": "#081414",
        "hero_gradient": "linear-gradient(135deg, #040a0a 0%, #081414 50%, #0e2424 100%)",
        "badge_bg": "rgba(45, 212, 191, 0.15)",
        "badge_text": "#2dd4bf",
    },
    "indigo": {
        "name": "نيلي نيون وريادة أعمال (Calm Slate / Neon Indigo)",
        "primary": "#818cf8",
        "primary_dark": "#4f46e5",
        "secondary": "#22d3ee",
        "accent": "#00f5a0",
        "neon_accent": "#818cf8",
        "neon_glow": "rgba(129, 140, 248, 0.25)",
        "bg_light": "#0c0f1d",
        "hero_gradient": "linear-gradient(135deg, #070914 0%, #0c0f1d 50%, #151b33 100%)",
        "badge_bg": "rgba(129, 140, 248, 0.15)",
        "badge_text": "#818cf8",
    },
    "crimson": {
        "name": "أحمر ليزر نيون هادئ (Calm Carbon / Neon Ruby Pulse)",
        "primary": "#f43f5e",
        "primary_dark": "#e11d48",
        "secondary": "#fbbf24",
        "accent": "#00f2fe",
        "neon_accent": "#f43f5e",
        "neon_glow": "rgba(244, 63, 94, 0.25)",
        "bg_light": "#14090b",
        "hero_gradient": "linear-gradient(135deg, #0a0405 0%, #14090b 50%, #241014 100%)",
        "badge_bg": "rgba(244, 63, 94, 0.15)",
        "badge_text": "#f43f5e",
    },
}

DEFAULT_CATALOGS = {
    "automotive": [
        {"title": "تسلا موديل 3 هاي لاند - دفع كلي كهربائي", "title_en": "Tesla Model 3 Highland Dual-Motor AWD", "price": 1850000, "category": "سيارات سيدان كهربائية", "category_en": "Electric Sedans", "badge": "تسليم فوري", "badge_en": "In Stock", "desc": "مدى سير يصل إلى 629 كم بالشحنة الواحدة، تسارع من 0 إلى 100 في 4.4 ثانية، قيادة ذاتية Autopilot وشاحن منزلي مجاني.", "desc_en": "Up to 629 km range per charge, 0-100 km/h in 4.4s, Autopilot capability with complimentary home charger.", "image_url": "https://images.unsplash.com/photo-1560958089-b8a1929cea89?auto=format&fit=crop&w=600&q=80"},
        {"title": "بي واي دي هان EV دفع رباعي فاخر", "title_en": "BYD Han EV Luxury AWD", "price": 1650000, "category": "سيارات سيدان كهربائية", "category_en": "Electric Sedans", "badge": "الأعلى تقييماً", "badge_en": "Top Rated", "desc": "بطارية Blade فائقة الأمان، مدى 605 كم، مقصورة جلدية فاخرة وأنظمة ذكاء اصطناعي متطورة مع ضمان 8 سنوات.", "desc_en": "Ultra-safe Blade battery, 605 km range, premium leather cabin, advanced ADAS with 8-year warranty.", "image_url": "https://images.unsplash.com/photo-1617788138017-80ad40651399?auto=format&fit=crop&w=600&q=80"},
        {"title": "فولكس فاجن ID.4 كروز - SUV عائلي كهربائي", "title_en": "Volkswagen ID.4 Crozz Electric SUV", "price": 1450000, "category": "سيارات SUV كهربائية", "category_en": "Electric SUVs", "badge": "الأكثر مبيعاً", "badge_en": "Best Seller", "desc": "سيارة SUV عائلية واسعة، مدى 550 كم، سقف بانوراما، شاشة ذكية متصلة وأنظمة أمان أوروبية معتمدة.", "desc_en": "Spacious family electric SUV, 550 km range, panoramic roof, intuitive cockpit, certified Euro NCAP safety.", "image_url": "https://images.unsplash.com/photo-1533473359331-0135ef1b58bf?auto=format&fit=crop&w=600&q=80"},
        {"title": "محطة شحن منزلي ذكية وول بوكس 22 كيلو واط", "title_en": "Smart Wallbox 22kW Home EV Charger", "price": 28500, "category": "شواحن وملحقات", "category_en": "Chargers & Accessories", "badge": "شحن سريع", "badge_en": "Fast Charging", "desc": "شاحن ذكي ثلاثي الطور Type 2 متوافق مع كافة السيارات الكهربائية مع تطبيق موبايل لمراقبة الشحن والاستهلاك.", "desc_en": "Three-phase Type 2 smart charger compatible with all EVs, mobile app tracking, IP65 waterproof.", "image_url": "https://images.unsplash.com/photo-1558441719-8b449c6ff4d3?auto=format&fit=crop&w=600&q=80"},
        {"title": "كابل شحن متنقل Type 2 فائق المتانة (5 متر)", "title_en": "Portable Type 2 Heavy-Duty Charging Cable (5m)", "price": 8500, "category": "شواحن وملحقات", "category_en": "Chargers & Accessories", "badge": "أصلي 100%", "badge_en": "100% Genuine", "desc": "كابل شحن سريع نحاسي نقي يتحمل حتى 32 أمبير مع حقيبة حمل أصلية مقاومة للصدمات والماء.", "desc_en": "Pure copper fast charging cable handling up to 32A, certified shockproof and waterproof carry case.", "image_url": "https://images.unsplash.com/photo-1619642751034-765dfdf7c58e?auto=format&fit=crop&w=600&q=80"},
        {"title": "باقة الفحص الشامل وضمان البطارية السنوي", "title_en": "Comprehensive EV & Battery Annual Inspection Package", "price": 4500, "category": "خدمات وضمانات", "category_en": "Services & Warranty", "badge": "خدمة معتمدة", "badge_en": "Certified", "desc": "فحص كمبيوتر تخصصي لخلايا البطارية، نظام التبريد السائل، الفرامل والمحركات مع تقرير معتمد.", "desc_en": "Specialized diagnostic scan for battery cells, thermal cooling loops, motors and certified health report.", "image_url": "https://images.unsplash.com/photo-1486006920555-c77dce18193b?auto=format&fit=crop&w=600&q=80"},
    ],
    "perfumes": [
        {"title": "دهن عود كمبودي ملكي معتق فاخر", "title_en": "Royal Aged Cambodian Dehn Al-Oud", "price": 850, "category": "عطور شرقية", "category_en": "Oriental Perfumes", "badge": "ثبات 48 ساعة", "badge_en": "48h Longevity", "desc": "دهن عود نقي مقطر على أصوله بنكهة بخورية سويتية فواحة وثبات لا مثيل له.", "desc_en": "Pure distilled Cambodian oud with a sweet smoky aroma and exceptional sillage.", "image_url": "https://images.unsplash.com/photo-1594035910387-fea47794261f?auto=format&fit=crop&w=600&q=80"},
        {"title": "عطر لافندر فرنسي مع مسك أبيض 100 مل", "title_en": "French Lavender & White Musk EDP (100ml)", "price": 450, "category": "عطور فرنسية", "category_en": "French Perfumes", "badge": "الأكثر مبيعاً", "badge_en": "Best Seller", "desc": "توليفة راقية من زهور اللافندر الفرنسية والمسك الأبيض والبرغموت المنعش.", "desc_en": "Elegant blend of French lavender blossoms, velvety white musk and crisp bergamot.", "image_url": "https://images.unsplash.com/photo-1547887537-6158d64c35b3?auto=format&fit=crop&w=600&q=80"},
        {"title": "تولة مسك الطهارة الأبيض الأصلي", "title_en": "Authentic Royal White Tahara Musk", "price": 180, "category": "زيوت وبخور", "category_en": "Oils & Incense", "badge": "طبيعي 100%", "badge_en": "100% Pure", "desc": "مسك مركز بقوام كثيف ورائحة نظافة ناعمة وفواحة تناسب الاستخدام اليومي.", "desc_en": "Thick concentrated white musk delivering a lasting fresh, clean signature scent.", "image_url": "https://images.unsplash.com/photo-1592945403244-b3fbafd7f539?auto=format&fit=crop&w=600&q=80"},
        {"title": "عطر عنبر نوار المركز إصدار خاص 100 مل", "title_en": "Amber Noir Intense Special Edition (100ml)", "price": 620, "category": "عطور شرقية", "category_en": "Oriental Perfumes", "badge": "فاخر ومميز", "badge_en": "Luxury Blend", "desc": "مزيج دافئ وغامض من العنبر الأسود وخشب الصندل والفانيليا المدخنة.", "desc_en": "Warm and magnetic fusion of black amber, creamy sandalwood and smoky vanilla.", "image_url": "https://images.unsplash.com/photo-1523293182086-7651a899d37f?auto=format&fit=crop&w=600&q=80"},
        {"title": "زيت الورد الجوري البلغاري الصافي النقي", "title_en": "Pure Bulgarian Damask Rose Essential Oil", "price": 320, "category": "زيوت وبخور", "category_en": "Oils & Incense", "badge": "قطفة أولى", "badge_en": "First Harvest", "desc": "خلاصة بتلات الورد الطبيعي النقي لتعطير الجسم والملابس بأفخم الروائح.", "desc_en": "Pure distilled rose petal essence for an ultra-luxurious, floral olfactory experience.", "image_url": "https://images.unsplash.com/photo-1615397349754-cfa2066a298e?auto=format&fit=crop&w=600&q=80"},
        {"title": "فواحة إلكترونية ذكية للسيارة والمكتب بالزيوت النقية", "title_en": "Smart Ultrasonic Car & Desk Aroma Diffuser", "price": 290, "category": "إكسسوارات عطرية", "category_en": "Accessories", "badge": "شحن Type-C", "badge_en": "USB-C", "desc": "فواحة ذكية بمستشعر اهتزاز تعمل تلقائياً مع رذاذ ناعم يدوم طوال اليوم.", "desc_en": "Smart sensor ultrasonic diffuser with automatic vibration on/off and ultra-fine mist.", "image_url": "https://images.unsplash.com/photo-1608571423902-eed4a5ad8108?auto=format&fit=crop&w=600&q=80"},
    ],
    "furniture": [
        {"title": "ركنة مودرن L-Shape قماش كتان تركي فاخر", "title_en": "Modern L-Shape Modular Turkish Linen Sofa", "price": 18500, "category": "غرف معيشة", "category_en": "Living Room", "badge": "الأكثر طلباً", "badge_en": "Best Seller", "desc": "هيكل خشب زان أحمر متين مع إسفنج سوفت ريبوند عالي الكثافة وقماش مقاوم للبقع.", "desc_en": "Solid red beech frame, high-density rebound foam, and stain-resistant Turkish linen.", "image_url": "https://images.unsplash.com/photo-1555041469-a586c61ea9bc?auto=format&fit=crop&w=600&q=80"},
        {"title": "مكتب تنفيذي مريح من خشب البلوط الطبيعي", "title_en": "Solid Oak Ergonomic Executive Desk", "price": 9500, "category": "أثاث مكتبي", "category_en": "Office Furniture", "badge": "تصميم عصري", "badge_en": "Modern Design", "desc": "مكتب عملي واسع مع فتحات كابلات ذكية وثلاثة أدراج تخزين بقفل مركزي.", "desc_en": "Spacious workspace with built-in cable management and three locking drawers.", "image_url": "https://images.unsplash.com/photo-1518455027359-f3f8164ba6bd?auto=format&fit=crop&w=600&q=80"},
        {"title": "سرير كينج مخملي هيدبورد كابوتنيه مع سحارة", "title_en": "King-Size Upholstered Velvet Storage Bed", "price": 14500, "category": "غرف نوم", "category_en": "Bedrooms", "badge": "تخزين هيدروليك", "badge_en": "Hydraulic Lift", "desc": "سرير مقاس 180×200 سم مع ميكانيزم هيدروليك قوي لتخزين واسع وتنجيد كابوتنيه فاخر.", "desc_en": "180x200cm bed with heavy-duty hydraulic lift storage and hand-tufted headboard.", "image_url": "https://images.unsplash.com/photo-1505693416388-ac5ce068fe85?auto=format&fit=crop&w=600&q=80"},
        {"title": "طقم طاولات قهوة مودرن بسطح رخامي فاخر (3 قطع)", "title_en": "Modern Marble-Top Nesting Coffee Tables (3 Pcs)", "price": 4800, "category": "غرف معيشة", "category_en": "Living Room", "badge": "رخام طبيعي", "badge_en": "Natural Marble", "desc": "قواعد معدنية مدهونة إلكتروستاتيك مقاومة للخدش مع أسطح رخامية أنيقة.", "desc_en": "Scratch-resistant electrostatic metal frames paired with elegant natural marble tops.", "image_url": "https://images.unsplash.com/photo-1533090161767-e6ffed986c88?auto=format&fit=crop&w=600&q=80"},
        {"title": "سفرة خشب زان طبيعي مع 6 كراسي مبطنة", "title_en": "Solid Beech Dining Table with 6 Padded Chairs", "price": 21500, "category": "غرف طعام", "category_en": "Dining Room", "badge": "خشب زان 100%", "badge_en": "100% Solid Wood", "desc": "طاولة سفرة مقاس 180×90 سم بتشطيب أستر مط مع 6 كراسي مريحة بتنجيد ممتاز.", "desc_en": "180x90cm dining table with matte finish and 6 ergonomic cushioned chairs.", "image_url": "https://images.unsplash.com/photo-1617806118233-18e1de247200?auto=format&fit=crop&w=600&q=80"},
        {"title": "وحدة أرفف ومكتبة كتب اسكندنافية عصرية", "title_en": "Scandinavian Multi-Tier Bookshelf & Display Unit", "price": 3600, "category": "ديكور وأرفف", "category_en": "Shelving & Decor", "badge": "سهل التركيب", "badge_en": "Easy Assembly", "desc": "تصميم هندسي مفتوح يجمع بين الخشب والمعدن لعرض الكتب والتحف بأناقة.", "desc_en": "Open geometric shelving blending wood and matte metal for stylish display.", "image_url": "https://images.unsplash.com/photo-1594938298603-c8148c4dae35?auto=format&fit=crop&w=600&q=80"},
    ],
    "books": [
        {"title": "موسوعة روائع الأدب العالمي الكلاسيكي (5 مجلدات)", "title_en": "World Classical Literature Masterpieces (5 Volumes)", "price": 480, "category": "روايات وأدب", "category_en": "Novels & Literature", "badge": "طبعة فاخرة", "badge_en": "Deluxe Edition", "desc": "مجموعة نادرة تضم أعظم الأعمال الأدبية الخالدة بترجمة عربية معتمدة وتجليد فاخر.", "desc_en": "Collector's boxset featuring timeless literary classics in certified Arabic translation.", "image_url": "https://images.unsplash.com/photo-1512820790803-83ca734da794?auto=format&fit=crop&w=600&q=80"},
        {"title": "دليل بناء العادات والنمو الشخصي المستدام", "title_en": "Sustainable Habit Mastery & Personal Growth Guide", "price": 160, "category": "تطوير الذات", "category_en": "Self-Development", "badge": "الأكثر مبيعاً", "badge_en": "Best Seller", "desc": "استراتيجيات عملية مثبتة علمياً لبناء عادات النجاح اليومية والتخلص من التسويف.", "desc_en": "Science-backed actionable frameworks to build high-performance daily habits.", "image_url": "https://images.unsplash.com/photo-1544716278-ca5e3f4abd8c?auto=format&fit=crop&w=600&q=80"},
        {"title": "كتاب ثورة الذكاء الاصطناعي وهندسة المستقبل", "title_en": "The Artificial Intelligence Revolution & Future Tech", "price": 195, "category": "علوم وتكنولوجيا", "category_en": "Science & Tech", "badge": "إصدار 2026", "badge_en": "2026 Edition", "desc": "تحليل شامل لنماذج الذكاء الاصطناعي التوليدي وتأثيرها على الوظائف وريادة الأعمال.", "desc_en": "In-depth guide on generative AI models, automation and their economic impact.", "image_url": "https://images.unsplash.com/photo-1526374965328-7f61d4dc18c5?auto=format&fit=crop&w=600&q=80"},
        {"title": "موسوعة تاريخ مصر والحضارة العربية المصورة", "title_en": "Illustrated History of Egypt & Arab Civilizations", "price": 350, "category": "تاريخ وثقافة", "category_en": "History & Culture", "badge": "مرجع موثق", "badge_en": "Authoritative", "desc": "توثيق شامل بالخرائط والصور التاريخية لمراحل الحضارة المصرية عبر العصور.", "desc_en": "Comprehensive historical reference enriched with archival maps and full-color photographs.", "image_url": "https://images.unsplash.com/photo-1461360370896-922624d12aa1?auto=format&fit=crop&w=600&q=80"},
        {"title": "دليل التركيز العميق ومضاعفة الإنتاجية اليومية", "title_en": "Deep Focus & 10x Productivity Handbook", "price": 140, "category": "تطوير الذات", "category_en": "Self-Development", "badge": "تطبيقي وعملي", "badge_en": "Practical", "desc": "كيف تحقق إنجاز شهر كامل في أسبوع واحد من خلال التحكم بالانتباه وإدارة الطاقة.", "desc_en": "Techniques to master attention control, eliminate distraction, and accelerate output.", "image_url": "https://images.unsplash.com/photo-1497633762265-9d179a990aa6?auto=format&fit=crop&w=600&q=80"},
        {"title": "مصباح قراءة مريح للعين مع فاصل جلدي أصلي", "title_en": "Eye-Care LED Reading Lamp with Genuine Leather Bookmark", "price": 220, "category": "إكسسوارات القراءة", "category_en": "Reading Accessories", "badge": "شحن USB", "badge_en": "Rechargeable", "desc": "إضاءة دافئة قابلة للتعديل بـ 3 درجات حرارة مع فاصل صفحات جلدي مصنع يدوياً.", "desc_en": "3-tone flicker-free reading clip light paired with a handcrafted genuine leather bookmark.", "image_url": "https://images.unsplash.com/photo-1507842229450-799d45e69e06?auto=format&fit=crop&w=600&q=80"},
    ],
    "gym": [
        {"title": "بروتين واي أيزوليت نقي 2 كجم شوكولاتة بلجيكية", "title_en": "Pure Whey Protein Isolate 2kg Belgian Chocolate", "price": 1850, "category": "مكملات غذائية", "category_en": "Supplements", "badge": "سريع الامتصاص", "badge_en": "Fast Absorbing", "desc": "27 جم بروتين صافي لكل سكوب، خالي من السكر والدهون واللاكتوز لدعم البناء العضلي.", "desc_en": "27g pure protein per scoop, zero added sugar, zero fat, lactose-free for lean muscle.", "image_url": "https://images.unsplash.com/photo-1579722821273-0f6c7d44362f?auto=format&fit=crop&w=600&q=80"},
        {"title": "كرياتين مونوهيدرات نقي ميكرونايزد 300 جم", "title_en": "Pure Micronized Creatine Monohydrate 300g", "price": 650, "category": "مكملات غذائية", "category_en": "Supplements", "badge": "أعلى نقاء", "badge_en": "100% Pure", "desc": "كرياتين معملي فائق النقاء لزيادة القوة البدنية وتحسين الاستشفاء والحجم العضلي.", "desc_en": "Creapure-grade micronized powder to dramatically boost power output and recovery.", "image_url": "https://images.unsplash.com/photo-1593095948071-474c5cc2989d?auto=format&fit=crop&w=600&q=80"},
        {"title": "مكمل طاقة وتركيز بومب باور قبل التمرين (30 جرعة)", "title_en": "Explosive Pre-Workout Pump Formula (30 Servings)", "price": 720, "category": "مكملات غذائية", "category_en": "Supplements", "badge": "طاقة جبارة", "badge_en": "High Stim", "desc": "تركيبة متطورة بالسيترولين والبيتا ألانين لضخ الدم والتركيز الذهني أثناء التمرين.", "desc_en": "Advanced citrulline and beta-alanine matrix for skin-splitting pumps and laser focus.", "image_url": "https://images.unsplash.com/photo-1517838277536-f5f99be501cd?auto=format&fit=crop&w=600&q=80"},
        {"title": "طقم دمبل ذكي سريع التعديل (2.5 إلى 24 كجم)", "title_en": "Quick-Select Adjustable Dumbbell (2.5kg - 24kg)", "price": 3800, "category": "أوزان ومعدات", "category_en": "Weights & Gear", "badge": "وفر مساحة", "badge_en": "Space Saver", "desc": "يغنيك عن 15 زوج دمبل بفضل نظام القفل والتدوير السريع المدمج مع قاعدة أمان.", "desc_en": "Replaces 15 pairs of dumbbells with a precision dial selector mechanism.", "image_url": "https://images.unsplash.com/photo-1584735935682-2f2b69dff9d2?auto=format&fit=crop&w=600&q=80"},
        {"title": "مجموعة أحبال مقاومة مطاطية احترافية (5 مستويات)", "title_en": "Heavy-Duty Multi-Level Resistance Bands Set", "price": 380, "category": "ملحقات رياضية", "category_en": "Fitness Accessories", "badge": "شامل الحقيبة", "badge_en": "Full Set", "desc": "تشمل 5 أحبال بمقاومات تصل إلى 150 رطل مع مقابض مريحة وحزام كاحل ومثبت باب.", "desc_en": "5 color-coded stackable tube bands up to 150 lbs with foam handles and door anchor.", "image_url": "https://images.unsplash.com/photo-1598289431512-b97b0917affc?auto=format&fit=crop&w=600&q=80"},
        {"title": "زجاجة شيكر ستانلس ستيل عازلة للحرارة 750 مل", "title_en": "Insulated Stainless Steel Shaker Bottle 750ml", "price": 340, "category": "ملحقات رياضية", "category_en": "Fitness Accessories", "badge": "مانع للتسريب", "badge_en": "Leak-Proof", "desc": "تصميم حراري يحفظ المشروبات باردة حتى 24 ساعة مع كرة خفق لمنع التكتل.", "desc_en": "Double-wall vacuum insulation keeping shakes ice-cold for 24 hours, BPA-free.", "image_url": "https://images.unsplash.com/photo-1544367567-0f2fcb009e0b?auto=format&fit=crop&w=600&q=80"},
    ],
    "pets": [
        {"title": "دراي فود سوبر بريميوم سلمون ودجاج (10 كجم)", "title_en": "Super Premium Salmon & Chicken Dry Food (10kg)", "price": 890, "category": "أغذية الحيوانات", "category_en": "Pet Food", "badge": "صحة الفراء", "badge_en": "Coat Health", "desc": "تركيبة غنية بالأوميجا 3 والبروتينات الحيوية لتعزيز المناعة وصحة الجهاز الهضمي.", "desc_en": "Rich in Omega-3 and easily digestible proteins for radiant coat and immune vitality.", "image_url": "https://images.unsplash.com/photo-1589924691995-400dc9ecc119?auto=format&fit=crop&w=600&q=80"},
        {"title": "سرير طبي مريح للحيوانات الأليفة مع غطاء قابل للغسل", "title_en": "Orthopedic Memory Foam Pet Bed (Washable Cover)", "price": 540, "category": "مستلزمات وعناية", "category_en": "Supplies & Care", "badge": "راحة فائقة", "badge_en": "Orthopedic", "desc": "حشوة ميموري فوم مريحة لدعم مفاصل الكلاب والقطط مع قماش مخملي مقاوم للخدش.", "desc_en": "High-density memory foam base to soothe joints with a removable, machine-washable plush cover.", "image_url": "https://images.unsplash.com/photo-1541599540903-216a46ca1dc0?auto=format&fit=crop&w=600&q=80"},
        {"title": "شجرة وبرج خدش وتسلق متعدد الطوابق للقطط", "title_en": "Multi-Level Sisal Cat Scratching Tree Tower", "price": 780, "category": "ألعاب وإكسسوارات", "category_en": "Toys & Scratchers", "badge": "أعمدة سيزال", "badge_en": "Natural Sisal", "desc": "تصميم قوي بارتفاع 120 سم مع كهف للنوم ومنصات مراقبة وأعمدة خدش متينة.", "desc_en": "120cm cat activity center with cozy condo, plush viewing perches, and sisal posts.", "image_url": "https://images.unsplash.com/photo-1545249390-6bdfa286032f?auto=format&fit=crop&w=600&q=80"},
        {"title": "نافورة مياه ذكية بفلتر كربوني 2.5 لتر للقطط والكلاب", "title_en": "Smart Ultra-Quiet Filtered Pet Water Fountain 2.5L", "price": 420, "category": "مستلزمات وعناية", "category_en": "Supplies & Care", "badge": "مضخة صامتة", "badge_en": "Ultra Quiet", "desc": "نظام فلترة رباعي ينقي المياه من الشوائب والروائح لتشجيع أليفك على الشرب الصحي.", "desc_en": "Quadruple filtration circulating water to entice pets to drink more clean, fresh water.", "image_url": "https://images.unsplash.com/photo-1583511655857-d19b40a7a54e?auto=format&fit=crop&w=600&q=80"},
        {"title": "لعبة ليزر ذكية تفاعلية للقطط بحركات عشوائية", "title_en": "Interactive Automatic Rotating Laser Cat Toy", "price": 280, "category": "ألعاب وإكسسوارات", "category_en": "Toys & Scratchers", "badge": "مؤقت تلقائي", "badge_en": "Auto Timer", "desc": "دوران بزوايا 360 درجة مع سرعات متعددة لتحفيز غريزة الصيد لدى القطط.", "desc_en": "360-degree rotating beam with random trajectory patterns to keep cats active.", "image_url": "https://images.unsplash.com/photo-1514888286974-6c03e2ca1dba?auto=format&fit=crop&w=600&q=80"},
        {"title": "مجموعة العناية الشاملة بالفراء وقص الأظافر", "title_en": "Complete Pet Grooming & De-Shedding Care Kit", "price": 260, "category": "مستلزمات وعناية", "category_en": "Supplies & Care", "badge": "طقم 5 قطع", "badge_en": "5-in-1 Kit", "desc": "فرشاة تنظيف ذاتية، مقص أظافر بمانع جروح، ومشط فك التشابك من الفولاذ المقاوم للصدأ.", "desc_en": "Self-cleaning slicker brush, safety nail clippers, and stainless steel dematting comb.", "image_url": "https://images.unsplash.com/photo-1548767797-d8c844163c4c?auto=format&fit=crop&w=600&q=80"},
    ],
    "honey": [
        {"title": "عسل سدر جبلي يمني دوعني نخب أول (كيلو)", "title_en": "Premium Yemeni Sidr Do'ani Mountain Honey (1kg)", "price": 420, "category": "عسل طبيعي فاخر", "category_en": "Luxury Natural Honey", "badge": "الأكثر طلباً", "badge_en": "Best Seller", "desc": "أجود أنواع السدر الجبلي الطبيعي المفحوص معملياً، غني بالمعادن ومضادات الأكسدة.", "desc_en": "Certified pure mountain Sidr honey, rich in minerals and antioxidants.", "image_url": "https://images.unsplash.com/photo-1587049352846-4a222e784d38?auto=format&fit=crop&w=600&q=80"},
        {"title": "عسل حبة البركة الصافي المنقى (نصف كيلو)", "title_en": "Pure Black Seed Honey (500g)", "price": 190, "category": "أعسال علاجية", "category_en": "Therapeutic Honey", "badge": "مقوي للمناعة", "badge_en": "Immunity Booster", "desc": "عسل نقي مغذى على أزهار حبة البركة، مثالي لتقوية الجهاز المناعي والجهاز التنفسي.", "desc_en": "Pure honey harvested from black seed blossoms, ideal for respiratory and immune support.", "image_url": "https://images.unsplash.com/photo-1587049352851-8d4e89133924?auto=format&fit=crop&w=600&q=80"},
        {"title": "عسل زهور الموالح الطبيعي (كيلو)", "title_en": "Natural Citrus Blossom Honey (1kg)", "price": 150, "category": "عسل الزهور", "category_en": "Floral Honey", "badge": "خفيف ولذيذ", "badge_en": "Light & Delicious", "desc": "عسل حمضيات خفيف ولذيذ وغني بفيتامين C، محبب جداً للأطفال وطاقة يومية طبيعية.", "desc_en": "Delicate citrus honey rich in Vitamin C, naturally energizing and loved by kids.", "image_url": "https://images.unsplash.com/photo-1582793988951-9aed5509eb97?auto=format&fit=crop&w=600&q=80"},
        {"title": "غذاء ملكات النحل الصافي الطازج (50 جم)", "title_en": "Fresh Pure Royal Jelly (50g)", "price": 240, "category": "مشتقات النحل", "category_en": "Bee Derivatives", "badge": "طاقة ونشاط", "badge_en": "Energy & Vitality", "desc": "غذاء ملكي نقي 100% مستخرج طازجاً، محفز طبيعي للنشاط الذهني والبدني.", "desc_en": "100% pure fresh royal jelly, a natural booster for physical and mental stamina.", "image_url": "https://images.unsplash.com/photo-1558642452-9d2a7deb7f62?auto=format&fit=crop&w=600&q=80"},
        {"title": "بوكس التوفير الملكي (3 برطمانات متنوعة + شمع)", "title_en": "Royal Savings Bundle (3 Jars + Natural Comb)", "price": 520, "category": "بكجات التوفير", "category_en": "Value Bundles", "badge": "وفر 25%", "badge_en": "Save 25%", "desc": "سدر جبلي + حبة بركة + زهور موالح + قطعة شمع طبيعي في علبة إهداء فاخرة.", "desc_en": "Sidr + Black Seed + Citrus honey + raw honeycomb in an elegant gift box.", "image_url": "https://images.unsplash.com/photo-1471864190281-a93a3070b6de?auto=format&fit=crop&w=600&q=80"},
        {"title": "شمع عسل نحل طبيعي قطفة أولى (نصف كيلو)", "title_en": "Raw Natural Honeycomb First Harvest (500g)", "price": 170, "category": "شمع العسل", "category_en": "Beeswax", "badge": "طبيعي 100%", "badge_en": "100% Natural", "desc": "إطارات شمع طبيعية مختومة خام بدون أي معالجة، تجربة تذوق ريفية أصيلة.", "desc_en": "Raw sealed virgin honeycomb frames without processing, an authentic rustic taste.", "image_url": "https://images.unsplash.com/photo-1587049352847-81a56d773cae?auto=format&fit=crop&w=600&q=80"},
    ],
    "restaurant": [
        {"title": "وجبة مشويات مشكلة مكس جريل (شخصين)", "title_en": "Mixed Charcoal Grill Platter for Two", "price": 240, "category": "مشويات الفحم", "category_en": "Charcoal Grills", "badge": "الأكثر طلباً", "badge_en": "Best Seller", "desc": "كباب، كفتة بلدي، شيش طاووق، مع أرز بسمتي وسلطات وخبز.", "desc_en": "Kebab, kofta, and shish tawook served with basmati rice, tahini, and warm bread.", "image_url": "https://images.unsplash.com/photo-1555939594-58d7cb561ad1?auto=format&fit=crop&w=600&q=80"},
        {"title": "طاجن ملوخية بالطشة واللحم البلدي", "title_en": "Traditional Egyptian Molokhia with Prime Beef", "price": 95, "category": "طواجن بلدي", "category_en": "Traditional Casseroles", "badge": "على أصوله", "badge_en": "Signature Dish", "desc": "ملوخية خضراء فريش بالسمن البلدي وقطع لحم كندوز فاخرة.", "desc_en": "Fresh green molokhia garlic-sautéed in farm butter with tender beef.", "image_url": "https://images.unsplash.com/photo-1546069901-ba9599a7e63c?auto=format&fit=crop&w=600&q=80"},
        {"title": "حواوشي بلدي سوبر بالجبنة الموتزاريلا", "title_en": "Crispy Egyptian Hawawshi with Melted Mozzarella", "price": 65, "category": "حواوشي ومخبوزات", "category_en": "Hawawshi & Bakery", "badge": "مقرمش وشهي", "badge_en": "Crispy & Cheesy", "desc": "لحم مفروم متبل بالخلطة السرية مع موتزاريلا سايحة.", "desc_en": "Spiced minced beef baked in crispy flatbread topped with molten mozzarella.", "image_url": "https://images.unsplash.com/photo-1565299624946-b28f40a0ae38?auto=format&fit=crop&w=600&q=80"},
        {"title": "نصف دجاجة مشوية على الفحم + أرز مبهر", "title_en": "Half Charcoal-Grilled Chicken with Spiced Rice", "price": 130, "category": "مشويات الفحم", "category_en": "Charcoal Grills", "badge": "وجبة التوفير", "badge_en": "Saver Meal", "desc": "دجاج متبل بخلطة الأعشاب يقدم مع الأرز والبطاطس والتومية.", "desc_en": "Herb-marinated grilled half chicken served with rice, fries, and garlic dip.", "image_url": "https://images.unsplash.com/photo-1598515214211-89d3c73ae83b?auto=format&fit=crop&w=600&q=80"},
        {"title": "سلطة طحينة وسلطة خضراء ومخلل مشكل", "title_en": "Assorted Oriental Salads & Pickles Platter", "price": 25, "category": "مقبلات وسلطات", "category_en": "Appetizers & Salads", "badge": "طازج", "badge_en": "Fresh Daily", "desc": "تشكيلة سلطات شرقية طازجة تكمل وجبتك المفضلة.", "desc_en": "Crisp garden salad, sesame tahini, and traditional Egyptian pickled vegetables.", "image_url": "https://images.unsplash.com/photo-1540420773420-3366772f4999?auto=format&fit=crop&w=600&q=80"},
    ],
    "vegetables": [
        {"title": "طماطم بلدي نخب أول (كيلو)", "title_en": "Grade-A Local Red Tomatoes (1kg)", "price": 18, "category": "خضار طازج", "category_en": "Fresh Vegetables", "badge": "طازج اليوم", "badge_en": "Farm Fresh", "desc": "طماطم سكرية مقطوفة صباحاً من مزارعنا بعناية فائقة.", "desc_en": "Naturally sweet red tomatoes picked fresh daily from Egyptian farms.", "image_url": "https://images.unsplash.com/photo-1592924357228-91a4daadcfea?auto=format&fit=crop&w=600&q=80"},
        {"title": "بطاطس تحمير سبونتا (كيلو)", "title_en": "Crispy Spunta Frying Potatoes (1kg)", "price": 20, "category": "خضار طازج", "category_en": "Fresh Vegetables", "badge": "ممتاز للتحمير", "badge_en": "Best for Frying", "desc": "حبات بطاطس منتقاة بجودة عالية وخالية من الشوائب.", "desc_en": "Hand-selected golden potatoes, ideal for crispy homemade fries.", "image_url": "https://images.unsplash.com/photo-1518977676601-b53f82aba655?auto=format&fit=crop&w=600&q=80"},
        {"title": "خيار صوب بلدي فريش (كيلو)", "title_en": "Fresh Local Greenhouse Cucumbers (1kg)", "price": 16, "category": "خضار طازج", "category_en": "Fresh Vegetables", "badge": "الأكثر طلباً", "badge_en": "Crisp & Crunchy", "desc": "خيار مقرمش طازج يومياً مناسب للسلطات والاستهلاك اليومي.", "desc_en": "Crunchy, sweet small greenhouse cucumbers perfect for healthy salads.", "image_url": "https://images.unsplash.com/photo-1604977042946-1eecc30f269e?auto=format&fit=crop&w=600&q=80"},
        {"title": "بصل أحمر بلدي فاخر (كيلو)", "title_en": "Premium Red Storage Onions (1kg)", "price": 22, "category": "خضار طازج", "category_en": "Fresh Vegetables", "badge": "جودة عالية", "badge_en": "High Quality", "desc": "بصل أحمر غني بالنكهة تخزين ممتاز.", "desc_en": "Pungent, flavorful local red onions carefully cured for long shelf life.", "image_url": "https://images.unsplash.com/photo-1618512496248-a07fe83aa8cb?auto=format&fit=crop&w=600&q=80"},
        {"title": "بوكس التوفير العائلي المشكل (10 كجم)", "title_en": "Family Fresh Produce Savings Box (10kg)", "price": 195, "category": "بوكسات التوفير", "category_en": "Savings Boxes", "badge": "وفر 25%", "badge_en": "Save 25%", "desc": "تشكيلة أسبوعية متكاملة (بطاطس، طماطم، بصل، خيار، كوسة، جزر).", "desc_en": "Weekly farm bundle including potatoes, tomatoes, onions, cucumbers, zucchini, carrots.", "image_url": "https://images.unsplash.com/photo-1540420773420-3366772f4999?auto=format&fit=crop&w=600&q=80"},
        {"title": "موز بلدي سكري فاخر (كيلو)", "title_en": "Sweet Egyptian Farm Bananas (1kg)", "price": 28, "category": "فواكه موسمية", "category_en": "Seasonal Fruits", "badge": "حلاوة طبيعية", "badge_en": "Naturally Sweet", "desc": "موز بلدي كامل النضج غني بالطاقة والبوتاسيوم.", "desc_en": "Ripe, creamy, honey-sweet local bananas packed with energy and potassium.", "image_url": "https://images.unsplash.com/photo-1571771894821-ce9b6c11b08e?auto=format&fit=crop&w=600&q=80"},
    ],
    "electronics": [
        {"title": "سماعة بلوتوث لاسلكية عازلة للضوضاء Pro", "title_en": "Wireless ANC Pro Bluetooth Headphones", "price": 450, "category": "صوتيات وسماعات", "category_en": "Audio & Headphones", "badge": "الأكثر مبيعاً", "badge_en": "Best Seller", "desc": "صوت نقي بتقنية Hi-Fi مع مايك مدمج وبطارية تدوم 24 ساعة متواصلة.", "desc_en": "Hi-Fi spatial audio with active noise cancellation and 24-hour battery life.", "image_url": "https://images.unsplash.com/photo-1590658268037-6bf12165a8df?auto=format&fit=crop&w=600&q=80"},
        {"title": "ساعة ذكية مقاومة للماء مع تتبع نبضات القلب", "title_en": "Waterproof Smartwatch with Heart-Rate Monitor", "price": 680, "category": "إلكترونيات ذكية", "category_en": "Smart Gadgets", "badge": "ضمان سنة", "badge_en": "1-Year Warranty", "desc": "شاشة أموليد لمسية، استقبال الإشعارات والمكالمات ومتابعة النشاط الرياضي.", "desc_en": "Vibrant AMOLED touchscreen, Bluetooth calling, and comprehensive fitness tracking.", "image_url": "https://images.unsplash.com/photo-1523275335684-37898b6baf30?auto=format&fit=crop&w=600&q=80"},
        {"title": "باور بانك شحن فائق السرعة 20,000 مللي أمبير", "title_en": "Ultra-Fast 20,000mAh Power Bank (22.5W)", "price": 390, "category": "شواحن وبطاريات", "category_en": "Chargers & Powerbanks", "badge": "شحن سريع 22.5W", "badge_en": "22.5W Fast Charge", "desc": "منافذ Type-C و USB متعددة لشحن 3 أجهزة في وقت واحد بأمان تام.", "desc_en": "Multi-port Type-C & USB outputs to charge 3 devices simultaneously with surge protection.", "image_url": "https://images.unsplash.com/photo-1609592424109-dd9892f1b177?auto=format&fit=crop&w=600&q=80"},
        {"title": "شاحن جداري GaN ثلاثي المنافذ 65W للابتوب والموبايل", "title_en": "65W GaN Triple-Port Fast Wall Charger", "price": 320, "category": "شواحن وبطاريات", "category_en": "Chargers & Powerbanks", "badge": "تقنية GaN", "badge_en": "GaN Technology", "desc": "شحن فائق السرعة متوافق مع الآيفون والسامسونج واللابتوب بحجم مدمج.", "desc_en": "Compact GaN charger compatible with laptops, tablets, iPhone, and Android.", "image_url": "https://images.unsplash.com/photo-1583863788434-e58a36330cf0?auto=format&fit=crop&w=600&q=80"},
    ],
    "fashion": [
        {"title": "قميص كلاسيك أوكسفورد قطن مصري 100%", "title_en": "Classic 100% Egyptian Cotton Oxford Shirt", "price": 320, "category": "ملابس رجالي", "category_en": "Men's Apparel", "badge": "قطن مصري 100%", "badge_en": "100% Egyptian Cotton", "desc": "خامة قطنية مريحة وناعمة، قصة سليم فيت عصرية مناسبة للعمل والمناسبات.", "desc_en": "Ultra-soft Egyptian cotton in a tailored slim-fit design for business and casual wear.", "image_url": "https://images.unsplash.com/photo-1596755094514-f87e34085b2c?auto=format&fit=crop&w=600&q=80"},
        {"title": "بنطلون جبردين إيطالي كلاسيك", "title_en": "Classic Italian Gabardine Trousers", "price": 380, "category": "ملابس رجالي", "category_en": "Men's Apparel", "badge": "الأكثر طلباً", "badge_en": "Best Seller", "desc": "أقمشة إيطالية مستوردة عالية الجودة ومقاومة للانكماش بتفصيل متقن.", "desc_en": "Tailored wrinkle-resistant gabardine fabric with a comfortable modern fit.", "image_url": "https://images.unsplash.com/photo-1624378439575-d8705ad7ae80?auto=format&fit=crop&w=600&q=80"},
        {"title": "سويت شيرت هودي أوفر سايز شتوي فاخر", "title_en": "Luxury Heavyweight Oversized Winter Hoodie", "price": 420, "category": "كاجوال شتوي", "category_en": "Winter Casual", "badge": "تريند 2026", "badge_en": "Trend 2026", "desc": "تقفيل فائق الجودة مع بطانة داخلية دافئة وخياطة مزدوجة فائقة المتانة.", "desc_en": "Fleece-lined heavyweight cotton with double-stitched seams and spacious kangaroo pocket.", "image_url": "https://images.unsplash.com/photo-1556905055-8f358a7a47b2?auto=format&fit=crop&w=600&q=80"},
        {"title": "تيشيرت بولو كاجوال قطن بيما ناعم", "title_en": "Pima Cotton Casual Polo Shirt", "price": 250, "category": "صيفي كاجوال", "category_en": "Summer Casual", "badge": "قطن ناعم", "badge_en": "Soft Cotton", "desc": "تيشيرت بولو أنيق بياقة متينة وملمس حريري يناسب الإطلالات اليومية.", "desc_en": "Silky smooth Pima cotton polo with durable ribbed collar and two-button placket.", "image_url": "https://images.unsplash.com/photo-1581655353564-df123a1eb820?auto=format&fit=crop&w=600&q=80"},
        {"title": "جاكيت جينز عصري أزرق غامق", "title_en": "Contemporary Dark Blue Denim Jacket", "price": 550, "category": "ملابس خارجية", "category_en": "Outerwear", "badge": "خامة ممتازة", "badge_en": "Premium Denim", "desc": "تصميم كلاسيكي متين مع جيوب أمامية وأزرار معدنية غير قابلة للصدأ.", "desc_en": "Durable raw denim with dual chest pockets and anti-rust brass buttons.", "image_url": "https://images.unsplash.com/photo-1576995853123-5a10305d93c0?auto=format&fit=crop&w=600&q=80"},
        {"title": "حذاء سنيكرز كاجوال جلد مريح", "title_en": "Comfortable Casual Leather Sneakers", "price": 490, "category": "أحذية وإكسسوارات", "category_en": "Shoes & Accessories", "badge": "راحة فائقة", "badge_en": "Ultra Comfortable", "desc": "نعل طبي مرن ومريح للمشي الطويل مع تصميم عصري يتماشى مع كافة الإطلالات.", "desc_en": "Orthopedic memory foam insole paired with a sleek, minimalist genuine leather upper.", "image_url": "https://images.unsplash.com/photo-1549298916-b41d501d3772?auto=format&fit=crop&w=600&q=80"},
    ],
    "clinic": [
        {"title": "كشف واستشارة طبية تخصصية شاملة", "title_en": "Comprehensive Medical Consultation & Diagnosis", "price": 250, "category": "الكشوفات الطبية", "category_en": "Medical Consultations", "badge": "حجز مسبق", "badge_en": "By Appointment", "desc": "فحص سريري دقيق، تشخيص الحالة، ووضع الخطة العلاجية المناسبة.", "desc_en": "Detailed clinical examination, accurate diagnosis, and personalized treatment plan."},
        {"title": "جلسة فحص ومتابعة دورية", "title_en": "Periodic Medical Follow-up Session", "price": 150, "category": "المتابعة الطبية", "category_en": "Follow-ups", "badge": "متابعة", "badge_en": "Follow-up", "desc": "متابعة تطور الحالة الصحية وتعديل الجرعات والعلاجات.", "desc_en": "Review of clinical progress and treatment/dosage adjustments."},
        {"title": "باقة الفحص الشامل الوقائي", "title_en": "Annual Preventive Health Screening Package", "price": 450, "category": "الفحص الوقائي", "category_en": "Preventative Checkups", "badge": "شامل", "badge_en": "All-Inclusive", "desc": "فحص وقائي كامل مع قياس المؤشرات الحيوية وتقرير شامل.", "desc_en": "Full screening with vital sign evaluation and diagnostic medical report."},
    ],
    "agency": [
        {"title": "باقة الانطلاق الرقمي (هوية بصرية + موقع متكامل)", "title_en": "Digital Launchpad (Branding & Full Web App)", "price": 3500, "category": "خدمات الشركات", "category_en": "Corporate Services", "badge": "الأكثر طلباً", "badge_en": "Most Popular", "desc": "تصميم الهوية والعلامة التجارية، وبرمجة تطبيق ويب متجاوب مع سلة طلبات وبوابات دفع.", "desc_en": "Brand identity design, responsive web app development with ordering and payments."},
        {"title": "إدارة الحملات الإعلانية الممولة (Google & Meta)", "title_en": "Paid Ad Campaigns Management (Google & Meta)", "price": 2200, "category": "التسويق الرقمي", "category_en": "Digital Marketing", "badge": "عائد مرتفع", "badge_en": "High ROI", "desc": "إعداد وإدارة الإعلانات على فيسبوك وإنستجرام وجوجل لاستهداف العملاء وتحقيق مبيعات.", "desc_en": "Targeted campaign setup and ongoing optimization across Meta and Google Ads."},
        {"title": "باقة التسويق والمحتوى الشاملة للمؤسسات", "title_en": "Enterprise Marketing & Content Strategy Package", "price": 5500, "category": "خدمات الشركات", "category_en": "Corporate Services", "badge": "نمو مستدام", "badge_en": "Sustainable Growth", "desc": "خطة تسويق شهري كاملة: إدارة السوشيال ميديا، كتابة الإعلانات، وتحسين محركات البحث SEO.", "desc_en": "Full monthly marketing engine: content creation, copy, social media and SEO growth."},
    ],
    "general": [
        {"title": "الباقة الأساسية المتميزة", "title_en": "Essential Core Package", "price": 350, "category": "الخدمات الأساسية", "category_en": "Core Services", "badge": "الأكثر طلباً", "badge_en": "Most Popular", "desc": "خدمة متكاملة تشمل الفحص والمتابعة والدعم الفني الكامل.", "desc_en": "End-to-end service package with inspection, follow-up, and technical support.", "image_url": "https://images.unsplash.com/photo-1472851294608-062f824d29cc?auto=format&fit=crop&w=600&q=80"},
        {"title": "الباقة المتقدمة الاحترافية", "title_en": "Advanced Professional Package", "price": 750, "category": "باقات احترافية", "category_en": "Pro Packages", "badge": "قيمة مضاعفة", "badge_en": "Double Value", "desc": "تشمل كافة المميزات مع أولوية التنفيذ وتوصيل مجاني.", "desc_en": "Includes all pro features with priority delivery and full service coverage.", "image_url": "https://images.unsplash.com/photo-1441986300917-64674bd600d8?auto=format&fit=crop&w=600&q=80"},
        {"title": "الخدمة السريعة الفورية", "title_en": "Express On-Demand Service", "price": 150, "category": "خدمات سريعة", "category_en": "Express Services", "badge": "فوري", "badge_en": "Instant", "desc": "تنفيذ عاجل خلال ساعات معدودة بأعلى معايير الدقة.", "desc_en": "Urgent expedited execution within hours to the highest standards.", "image_url": "https://images.unsplash.com/photo-1526170375885-4d8ecf77b99f?auto=format&fit=crop&w=600&q=80"},
    ],
    "portfolio": [
        {"title": "اختبار اختراق تطبيقات الويب والـ APIs (Web Pentest)", "title_en": "Web Application & API Penetration Testing", "price": 2500, "category": "خدمات الفحص الأمني", "category_en": "Security Auditing", "badge": "شامل التقرير", "badge_en": "Full Report", "desc": "فحص أمني عميق وكشف ثغرات OWASP Top 10 و Business Logic مع تقديم تقرير تفصيلي بالحلول.", "desc_en": "Deep vulnerability assessment covering OWASP Top 10 with actionable remediation roadmap."},
        {"title": "تدقيق أمني للبنية التحتية والسيرفرات (Infra Audit)", "title_en": "Cloud Infrastructure & Server Hardening Audit", "price": 3500, "category": "خدمات الفحص الأمني", "category_en": "Security Auditing", "badge": "موصى به للشركات", "badge_en": "Recommended", "desc": "تقييم أمان الخوادم السحابية، جدران الحماية Firewall، وضبط تكوينات الحماية Hardening.", "desc_en": "Evaluation of cloud servers, firewall policies, IAM configurations, and container hardening."},
        {"title": "استشارة أمنية وتقييم المخاطر السيبرانية (Consultation)", "title_en": "Cybersecurity Strategy & Risk Consultation", "price": 1000, "category": "استشارات وتوجيه", "category_en": "Consulting", "badge": "فوري", "badge_en": "Instant", "desc": "جلسة فنية لتحليل بنيتك الرقمية ووضع خطة تأمين متكاملة متوافقة مع المعايير القياسية.", "desc_en": "Technical advisory session to assess digital architecture and map defense roadmaps."},
        {"title": "تأمين الحسابات ومكافحة الهندسة الاجتماعية (Hardening)", "title_en": "Account Security & Anti-Phishing Hardening", "price": 1200, "category": "حلول الحماية", "category_en": "Protection Solutions", "badge": "دعم فني", "badge_en": "Support", "desc": "تفعيل آليات 2FA/MFA، تدريب الفريق ضد رسائل التصيد Phishing، وتأمين البريد المؤسسي.", "desc_en": "MFA implementation, employee anti-phishing defense drills, and enterprise email security."},
    ],
    "portfolio_ai": [
        {"title": "بناء وهندسة أنظمة الوكلاء الأذكياء (Autonomous AI Agents)", "title_en": "Autonomous AI Agents Architecture & Tool Calling", "price": 4500, "category": "أنظمة الذكاء الاصطناعي", "category_en": "AI Systems", "badge": "الأكثر طلباً", "badge_en": "Best Seller", "desc": "تصميم وبرمجة وكلاء أذكياء مستقلين لأتمتة المهام المعقدة، اتخاذ القرارات وربط النماذج بالأدوات وقواعد البيانات.", "desc_en": "Architecting autonomous multi-agent systems, decision engines, structured tool calling, and workflow automation."},
        {"title": "تطوير وتدريب نماذج التعلم العميق (Deep Learning & Vision)", "title_en": "Deep Learning & Vision Transformer Training", "price": 6000, "category": "التعلم العميق", "category_en": "Deep Learning", "badge": "موصى به للمؤسسات", "badge_en": "Enterprise", "desc": "تدريب وتخصيص نماذج PyTorch و TensorFlow للرؤية الحاسوبية ومعالجة اللغات الطبيعية وحل المشكلات المعقدة.", "desc_en": "Training and fine-tuning PyTorch & TensorFlow models for computer vision, defect detection, and custom NLP."},
        {"title": "بناء قواعد معرفية وأنظمة استرجاع متقدمة (Enterprise RAG)", "title_en": "Enterprise Vector DB & Hybrid RAG Pipelines", "price": 3800, "category": "حلول الذكاء الاصطناعي", "category_en": "AI Solutions", "badge": "فائق السرعة", "badge_en": "High Speed", "desc": "هندسة محركات بحث دلالي وقواعد بيانات متجهية (Vector Databases) للبحث في وثائق وبيانات الشركات بدقة عالية.", "desc_en": "Building semantic search engines and vector retrieval pipelines for reliable enterprise question-answering."},
        {"title": "استشارات هندسة الذكاء الاصطناعي وتسريع الاستدلال (MLOps)", "title_en": "AI Architecture & MLOps Optimization Advisory", "price": 2000, "category": "استشارات وتوجيه", "category_en": "Consulting", "badge": "فوري", "badge_en": "Instant", "desc": "جلسة فنية لتقييم جدوى مشاريع الـ AI، تحسين سرعة النماذج عبر TensorRT، ونشرها على السحابة بأقل تكلفة.", "desc_en": "Technical advisory on model optimization, TensorRT inference speedup, and scalable cloud deployment."},
    ],
    "portfolio_dev": [
        {"title": "تطوير منصات وتطبيقات الويب المتكاملة (Full-Stack Platforms)", "title_en": "Full-Stack Web Application Development", "price": 4000, "category": "تطوير برمجيات", "category_en": "Software Development", "badge": "شامل الواجهات والباك إند", "badge_en": "End-to-End", "desc": "برمجة منصات وتطبيقات سحابية كاملة من واجهات المستخدم التفاعلية الحديثة حتى خوادم الـ Backend وقواعد البيانات.", "desc_en": "End-to-end web platform engineering with modern reactive UIs, secure REST/GraphQL APIs, and resilient data layers."},
        {"title": "بناء وتوثيق واجهات برمجة التطبيقات (High-Scale Microservices)", "title_en": "High-Performance API & Microservices Architecture", "price": 3000, "category": "هندسة الأنظمة", "category_en": "System Architecture", "badge": "عالي الأداء", "badge_en": "High Scale", "desc": "تصميم وبناء خدمات برمجية ميكروية فائقة السرعة بـ Python و Node.js مع توثيق OpenAPI/Swagger واختبارات شاملة.", "desc_en": "Designing resilient, scalable microservices and APIs with high concurrency, OpenAPI docs, and automated tests."},
        {"title": "تسريع أداء التطبيقات وهيكلة قواعد البيانات (DB & Optimization)", "title_en": "Database Indexing & Performance Optimization", "price": 2200, "category": "تحسين الأداء", "category_en": "Performance", "badge": "تحسين 10x", "badge_en": "10x Speedup", "desc": "فحص الاختناقات وتسريع استعلامات SQL المعقدة، تطبيق آليات التخزين المؤقت Redis، وتحسين زمن الاستجابة.", "desc_en": "Eliminating bottlenecks, SQL query profiling, Redis caching implementation, and sub-50ms latency tuning."},
        {"title": "مراجعة الأكواد والاستشارات المعمارية (Code Review & Advisory)", "title_en": "Software Architecture Consulting & Code Review", "price": 1500, "category": "استشارات برمجية", "category_en": "Dev Advisory", "badge": "تقرير جودة", "badge_en": "Audit Report", "desc": "مراجعة تفصيلية لجودة الكود، تطبيق مبادئ Clean Architecture و SOLID، وخطة للتوسع المستقبلي.", "desc_en": "In-depth code quality audit, Clean Architecture guidelines, refactoring roadmaps, and security best practices."},
    ],
    "portfolio_design": [
        {"title": "تصميم أنظمة وتطبيقات متكاملة (UI/UX & Design Systems)", "title_en": "Full Product UI/UX Design & Design Systems", "price": 3500, "category": "تصميم واجهات وتجربة المستخدم", "category_en": "UI/UX Design", "badge": "الأكثر طلباً", "badge_en": "Best Seller", "desc": "بناء تجارب مستخدم متكاملة على Figma، شاشات متجاوبة، ومكونات تصميمية قابلة لإعادة الاستخدام مع إرشادات التسليم للمطورين.", "desc_en": "End-to-end Figma UX flows, responsive component libraries, and clean handoff specs for engineering teams."},
        {"title": "أبحاث تجربة المستخدم واختبارات القابلية (User Research & Testing)", "title_en": "User Research, Personas & Usability Testing", "price": 2500, "category": "أبحاث وتجربة المستخدم", "category_en": "User Research", "badge": "مبني على بيانات", "badge_en": "Data-Driven", "desc": "إجراء مقابلات المستخدمين، بناء رحلات العميل Customer Journeys، وتحليل قابلية الاستخدام لرفع معدلات التحويل.", "desc_en": "User interviews, persona synthesis, customer journey maps, and heuristic evaluations to maximize conversion."},
        {"title": "نماذج تفاعلية عالية الدقة والرسوم المتحركة (Interactive Prototyping)", "title_en": "High-Fidelity Interactive Prototypes & Motion", "price": 2000, "category": "نماذج تفاعلية", "category_en": "Interactive Prototypes", "badge": "تفاعلي 100%", "badge_en": "Interactive", "desc": "بروتوتايب تفاعلي حي يحاكي التطبيق النهائي بدقة على Figma مع انتقالات سلسة وحركات ميكرو Micro-interactions.", "desc_en": "Pixel-perfect clickable Figma prototypes with smooth micro-interactions and realistic user flows."},
        {"title": "إعادة تصميم وتدقيق تجربة الاستخدام (UI/UX Audit & Redesign)", "title_en": "UX Heuristic Audit & Product Redesign", "price": 1800, "category": "استشارات وتدقيق التصميم", "category_en": "Design Advisory", "badge": "تقرير شامل", "badge_en": "Audit Report", "desc": "فحص شامل للمنتج الحالي، كشف نقاط الاحتكاك ومشاكل الواجهات، وتقديم مقترحات إعادة تصميم فورية قابلة للتطبيق.", "desc_en": "Deep heuristic review of current products, UX friction identification, and quick-win redesign mockups."},
    ]
}

CATEGORY_TRANS = {
    # Automotive
    "سيارات سيدان كهربائية": "Electric Sedans",
    "سيارات SUV كهربائية": "Electric SUVs",
    "شواحن وملحقات": "Chargers & Accessories",
    "خدمات وضمانات": "Services & Warranty",
    "سيارات كهربائية": "Electric Vehicles",
    "قطع غيار": "Spare Parts",
    # Honey
    "عسل طبيعي فاخر": "Luxury Natural Honey",
    "أعسال علاجية": "Therapeutic Honey",
    "عسل الزهور": "Floral Honey",
    "مشتقات النحل": "Bee Derivatives",
    "بكجات التوفير": "Value Bundles",
    "شمع العسل": "Beeswax",
    # Vegetables
    "خضار طازج": "Fresh Vegetables",
    "فواكه موسمية": "Seasonal Fruits",
    "بوكسات التوفير": "Savings Boxes",
    # Restaurant
    "مشويات الفحم": "Charcoal Grills",
    "طواجن بلدي": "Traditional Casseroles",
    "حواوشي ومخبوزات": "Hawawshi & Bakery",
    "مقبلات وسلطات": "Appetizers & Salads",
    "وجبات فردية": "Individual Meals",
    # Electronics
    "صوتيات وسماعات": "Audio & Headphones",
    "إلكترونيات ذكية": "Smart Gadgets",
    "شواحن وبطاريات": "Chargers & Powerbanks",
    # Fashion
    "ملابس رجالي": "Men's Apparel",
    "كاجوال شتوي": "Winter Casual",
    "صيفي كاجوال": "Summer Casual",
    "ملابس خارجية": "Outerwear",
    "أحذية وإكسسوارات": "Shoes & Accessories",
    # Clinic
    "الكشوفات الطبية": "Medical Consultations",
    "المتابعة الطبية": "Follow-ups",
    "الفحص الوقائي": "Preventative Checkups",
    # Agency
    "خدمات الشركات": "Corporate Services",
    "التسويق الرقمي": "Digital Marketing",
    # Perfumes
    "عطور شرقية": "Oriental Perfumes",
    "عطور فرنسية": "French Perfumes",
    "زيوت وبخور": "Oils & Incense",
    "إكسسوارات عطرية": "Accessories",
    # Furniture
    "غرف معيشة": "Living Room",
    "أثاث مكتبي": "Office Furniture",
    "غرف نوم": "Bedrooms",
    "غرف طعام": "Dining Room",
    "ديكور وأرفف": "Shelving & Decor",
    # Books
    "روايات وأدب": "Novels & Literature",
    "تطوير الذات": "Self-Development",
    "علوم وتكنولوجيا": "Science & Tech",
    "تاريخ وثقافة": "History & Culture",
    "إكسسوارات القراءة": "Reading Accessories",
    # Gym
    "مكملات غذائية": "Supplements",
    "أوزان ومعدات": "Weights & Gear",
    "ملحقات رياضية": "Fitness Accessories",
    # Pets
    "أغذية الحيوانات": "Pet Food",
    "مستلزمات وعناية": "Supplies & Care",
    "ألعاب وإكسسوارات": "Toys & Scratchers",
    # General
    "الخدمات الأساسية": "Core Services",
    "باقات احترافية": "Pro Packages",
    "خدمات سريعة": "Express Services",
    # AI Portfolio
    "أنظمة الذكاء الاصطناعي": "AI Systems",
    "التعلم العميق": "Deep Learning",
    "حلول الذكاء الاصطناعي": "AI Solutions",
    # Dev Portfolio
    "تطوير برمجيات": "Software Development",
    "هندسة الأنظمة": "System Architecture",
    "تحسين الأداء": "Performance",
    "استشارات برمجية": "Dev Advisory",
    # UI/UX Portfolio
    "تصميم واجهات وتجربة المستخدم": "UI/UX Design",
    "أبحاث وتجربة المستخدم": "User Research",
    "نماذج تفاعلية": "Interactive Prototypes",
    "استشارات وتدقيق التصميم": "Design Advisory",
    "الكل": "All",
    "عام": "General",
}

BADGE_TRANS = {
    "الأكثر طلباً": "Most Popular",
    "الأكثر مبيعاً": "Best Seller",
    "مبني على بيانات": "Data-Driven",
    "تفاعلي 100%": "100% Interactive",
    "تقرير شامل": "Full Audit",
    "شامل التقرير": "Full Report",
    "موصى به للشركات": "Recommended",
    "موصى به للمؤسسات": "Enterprise",
    "شامل الواجهات والباك إند": "End-to-End",
    "عالي الأداء": "High Scale",
    "تحسين 10x": "10x Speedup",
    "تقرير جودة": "Audit Report",
    "فائق السرعة": "High Speed",
    "الأعلى تقييماً": "Top Rated",
    "تسليم فوري": "In Stock",
    "شحن سريع": "Fast Delivery",
    "أصلي 100%": "100% Genuine",
    "خدمة معتمدة": "Certified",
    "طبيعي 100%": "100% Natural",
    "مقوي للمناعة": "Immunity Booster",
    "خفيف ولذيذ": "Light & Delicious",
    "طاقة ونشاط": "Energy & Vitality",
    "وفر 25%": "Save 25%",
    "وفر 20%": "Save 20%",
    "طازج اليوم": "Fresh Today",
    "ممتاز للتحمير": "Best for Frying",
    "جودة عالية": "High Quality",
    "حلاوة طبيعية": "Naturally Sweet",
    "على أصوله": "Signature",
    "مقرمش وشهي": "Crispy & Tasty",
    "وجبة التوفير": "Saver Meal",
    "طازج": "Fresh",
    "ضمان سنة": "1-Year Warranty",
    "تقنية GaN": "GaN Tech",
    "حجز مسبق": "Advance Booking",
    "متابعة": "Follow-up",
    "شامل": "All-Inclusive",
    "نمو مستدام": "Sustainable Growth",
    "عائد مرتفع": "High ROI",
    "قطن مصري 100%": "100% Egyptian Cotton",
    "تريند 2026": "Trend 2026",
    "قطن ناعم": "Soft Cotton",
    "خامة ممتازة": "Premium Fabric",
    "راحة فائقة": "Ultra Comfortable",
    "قيمة مضاعفة": "Double Value",
    "فوري": "Instant",
    "شامل التقرير": "Full Report Included",
    "موصى به للشركات": "Recommended",
    "دعم فني": "Technical Support",
    "ثبات 48 ساعة": "48h Longevity",
    "فاخر ومميز": "Luxury Blend",
    "قطفة أولى": "First Harvest",
    "شحن Type-C": "USB-C",
    "تصميم عصري": "Modern Design",
    "تخزين هيدروليك": "Hydraulic Lift",
    "رخام طبيعي": "Natural Marble",
    "خشب زان 100%": "100% Solid Wood",
    "سهل التركيب": "Easy Assembly",
    "طبعة فاخرة": "Deluxe Edition",
    "إصدار 2026": "2026 Edition",
    "مرجع موثق": "Authoritative",
    "تطبيقي وعملي": "Practical",
    "شحن USB": "USB Rechargeable",
    "سريع الامتصاص": "Fast Absorbing",
    "أعلى نقاء": "100% Pure",
    "طاقة جبارة": "High Stim",
    "وفر مساحة": "Space Saver",
    "مانع للتسريب": "Leak-Proof",
    "صحة الفراء": "Coat Health",
    "أعمدة سيزال": "Natural Sisal",
    "مضخة صامتة": "Ultra Quiet",
    "مؤقت تلقائي": "Auto Timer",
    "طقم 5 قطع": "5-in-1 Kit",
}


CATALOG_TITLE_MAP = {}
CATALOG_DESC_MAP = {}
for _n_items in DEFAULT_CATALOGS.values():
    for _item in _n_items:
        _ar_t = _item.get("title")
        _en_t = _item.get("title_en")
        _ar_d = _item.get("desc") or _item.get("description")
        _en_d = _item.get("desc_en")
        if _ar_t and _en_t:
            CATALOG_TITLE_MAP[_ar_t.strip()] = _en_t.strip()
        if _ar_d and _en_d:
            CATALOG_DESC_MAP[_ar_d.strip()] = _en_d.strip()


def _normalize_store_items(raw_items: list, niche: str) -> list:
    """Normalize catalog items ensuring all bilingual fields exist."""
    normalized = []
    for i, it in enumerate(raw_items):
        it_dict = dict(it)
        title_ar = str(it_dict.get("title") or f"منتج {i + 1}").strip()
        cat_ar = str(it_dict.get("category") or "الكل").strip()
        badge_ar = str(it_dict.get("badge") or "").strip()
        desc_ar = str(it_dict.get("description") or it_dict.get("desc") or "").strip()
        price = _safe_price(it_dict.get("price", 0))
        img = str(it_dict.get("image_url") or "").strip()

        title_en = str(it_dict.get("title_en") or "").strip()
        if not title_en or title_en == title_ar:
            if title_ar in CATALOG_TITLE_MAP:
                title_en = CATALOG_TITLE_MAP[title_ar]
            else:
                for k, v in CATALOG_TITLE_MAP.items():
                    if k in title_ar or title_ar in k:
                        title_en = v
                        break
                else:
                    title_en = title_ar

        cat_en = str(it_dict.get("category_en") or "").strip()
        if not cat_en:
            cat_en = CATEGORY_TRANS.get(cat_ar, cat_ar)

        badge_en = str(it_dict.get("badge_en") or "").strip()
        if not badge_en and badge_ar:
            badge_en = BADGE_TRANS.get(badge_ar, badge_ar)

        desc_en = str(it_dict.get("desc_en") or it_dict.get("description_en") or "").strip()
        if not desc_en or desc_en == desc_ar:
            if desc_ar in CATALOG_DESC_MAP:
                desc_en = CATALOG_DESC_MAP[desc_ar]
            else:
                for k, v in CATALOG_DESC_MAP.items():
                    if k in desc_ar or desc_ar in k:
                        desc_en = v
                        break
                else:
                    desc_en = desc_ar or "Certified premium quality item."

        normalized.append({
            "id": i + 1,
            "title": title_ar,
            "title_en": title_en,
            "price": price,
            "category": cat_ar,
            "category_en": cat_en,
            "badge": badge_ar,
            "badge_en": badge_en,
            "description": desc_ar,
            "desc_en": desc_en,
            "image_url": img
        })
    return normalized


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

    # 2. Automotive & Electric Vehicles
    if any(k in t for k in [
        "سيار", "سياره", "سيارة", "عربيات", "اوتو", "مركبات",
        "تسلا", "قطع غيار", "شواحن سيارات",
        "معرض سيارات", "بيع سيارات", "car", "cars", "automotive", "motor"
    ]) or ("كهربائ" in t and ("سيار" in t or "عرب" in t or "مركب" in t)):
        return "automotive"

    # 3. Perfumes & Fragrances
    if any(k in t for k in [
        "عطور", "عطر", "برفان", "بخور", "عود", "مسك", "روائح", "عطورات", "perfume", "fragrance"
    ]):
        return "perfumes"

    # 4. Furniture & Interior Decor
    if any(k in t for k in [
        "اثاث", "أثاث", "مفروشات", "ديكور", "غرف نوم", "انتريه", "صالون", "مطابخ", "furniture"
    ]):
        return "furniture"

    # 5. Books & Literature
    if any(k in t for k in [
        "كتب", "كتاب", "روايات", "مكتبة", "مكتبه", "قرطاسية", "book", "books"
    ]):
        return "books"

    # 6. Gym, Fitness & Supplements
    if any(k in t for k in [
        "جيم", "مكملات", "بروتين", "لياقة", "رياضة", "فتنس", "gym", "fitness"
    ]):
        return "gym"

    # 7. Pets & Animal Supplies
    if any(k in t for k in [
        "حيوانات", "قطط", "كلاب", "طيور", "بت شوب", "حيوان أليف", "pet", "pets"
    ]):
        return "pets"

    # 8. Honey & Organic Bee Products
    if any(k in t for k in ["عسل", "نحل", "سدر", "شمع", "غذاء ملكات", "حبة البركة", "مناحل", "منحل"]):
        return "honey"

    # 9. Medical, Doctors, Clinics
    if any(k in t for k in ["عياد", "دكتور", "طبيب", "اسنان", "أسنان", "علاج", "مستشفى", "مركز طبي"]):
        return "clinic"

    # 10. Agencies, Companies, SaaS
    if any(k in t for k in ["وكالة", "شركة", "agency", "تسويق", "حلول برمجية", "استشارات", "saas", "سيرفيس"]):
        return "agency"

    # 11. Food, Cafes, Grills, Restaurants
    if any(k in t for k in ["مطعم", "أكل", "اكل", "كافيه", "قهوة", "مقهى", "برجر", "مشويات", "كباب", "حواوشي", "وجبات", "حلويات", "شاورما", "شيف", "بيتزا"]):
        return "restaurant"

    # 12. Fresh Produce, Vegetables, Fruits, Groceries
    if any(k in t for k in ["خضار", "فواكه", "طماطم", "بصل", "سوق", "مزرعة", "عضوي", "محصول", "أغذية طازجة", "سوبرماركت", "بقالة"]):
        return "vegetables"

    # 13. Fashion, Clothing, Boutiques
    if any(k in t for k in ["ملابس", "ازياء", "أزياء", "بوتيك", "فاشون", "احذية", "شنط", "عبايات"]):
        return "fashion"

    # 14. Tech, Gadgets, Electronics
    if any(k in t for k in ["الكترون", "اجهز", "موبايل", "هواتف", "سماعات", "كمبيوتر", "لابتوب", "شواحن", "ساعات ذكية", "تكنو"]):
        return "electronics"

    return "general"


def detect_portfolio_track(context: str) -> str:
    """Infers the specialized professional track for a portfolio: 'ai', 'dev', 'design', or 'cyber'."""
    ctx = (context or "").lower()
    if any(k in ctx for k in [
        "ui", "ux", "ui/ux", "ui-ux", "تصميم واجهات", "تجربة المستخدم",
        "figma", "فوتوشوب", "ديزاين", "ديزاينر", "مصمم", "تغذية بصرية",
        "wireframe", "prototype", "design system", "user research", "case study"
    ]):
        return "design"
    elif any(k in ctx for k in [
        "ai", "ذكاء اصطناعي", "machine learning", "deep learning",
        "تعلم آلة", "تعلم العميق", "ديب ليرنينج", "data science",
        "علم بيانات", "وكلاء ذكاء", "وكيل ذكي", "وكلاء مستقلين",
        "llm", "neural", "vision transformer", "nlp"
    ]):
        return "ai"
    elif any(k in ctx for k in [
        "برمج", "مطور", "مبرمج", "ويب", "software", "developer",
        "full stack", "fullstack", "frontend", "backend", "كود",
        "حلول رقمية", "تطوير تطبيقات", "mobile app"
    ]) and not any(k in ctx for k in ["سايبر", "سيكيورتي", "أمن", "امن", "اختراق", "pentest"]):
        return "dev"
    return "cyber"


def get_default_catalog(niche: str, context: str = "") -> list:
    """Retrieves default catalog items tailored to niche and portfolio specialization track."""
    if niche == "portfolio":
        track = detect_portfolio_track(context)
        if track == "design":
            return DEFAULT_CATALOGS.get("portfolio_design", DEFAULT_CATALOGS["portfolio"])
        elif track == "ai":
            return DEFAULT_CATALOGS.get("portfolio_ai", DEFAULT_CATALOGS["portfolio"])
        elif track == "dev":
            return DEFAULT_CATALOGS.get("portfolio_dev", DEFAULT_CATALOGS["portfolio"])
        return DEFAULT_CATALOGS["portfolio"]
    return DEFAULT_CATALOGS.get(niche, DEFAULT_CATALOGS["general"])


def build_site_html(job_id: int, client: str, request: str, settings: dict = None, items: list = None) -> str:
    """Master synthesizer: delegates to specialized archetype generators."""
    settings = settings or {}
    items = items or []

    niche = detect_niche(request + " " + client + " " + (settings.get("category") or ""))

    if niche == "portfolio":
        document = build_portfolio_html(job_id, client, request, settings, items)
    else:
        document = build_store_html(job_id, client, request, settings, items, niche)

    issues = artifacts.validate_site_html(document)
    if issues:
        raise RuntimeError("Generated template failed artifact validation: " + "; ".join(issues))
    return document


def build_portfolio_html(job_id: int, client: str, request: str, settings: dict = None, items: list = None) -> str:
    """Generates an elite dark/light mode Cybersecurity, AI & Tech Portfolio SPA with bilingual support."""
    settings = settings or {}
    items = items or []

    # Detect professional track: ai, dev, or cyber
    ctx_full = f"{request} {client} {settings.get('brand_name') or ''} {settings.get('category') or ''}".strip()
    track = detect_portfolio_track(ctx_full)

    # Extract candidate name
    default_name = (
        "ياسين أحمد | Yaseen Ahmed" if track == "cyber"
        else ("عمر مختار | Omar Mokhtar" if track == "design"
        else ("الفاروق إبراهيم | Alfarouq Ibrahim" if track == "ai"
        else "أحمد محمود | Ahmed Mahmoud"))
    )
    brand_name = _safe_text(settings.get("brand_name") or client, default_name, 120)
    if brand_name.startswith("tg:"):
        brand_name = default_name

    pal = PALETTES["royal"] if track == "design" else PALETTES["cyber"]
    primary = _safe_hex_color(settings.get("color_primary"), pal["primary"])
    secondary = _safe_hex_color(settings.get("color_secondary"), pal["secondary"])
    accent = pal["accent"]

    phone = _safe_phone(settings.get("phone"))
    whatsapp = _safe_phone(settings.get("whatsapp"), phone)
    clean_wa = re.sub(r"[^\d]", "", whatsapp)
    if clean_wa.startswith("01"):
        clean_wa = "2" + clean_wa
    if clean_wa:
        portfolio_contact_cta = f'''<a href="https://wa.me/{clean_wa}?text={html.escape('مرحباً ' + brand_name + '، أود مناقشة مشروع.')}" target="_blank" rel="noopener" class="px-8 py-3.5 rounded-xl bg-slate-900 border border-slate-700 hover:border-cyan-500 text-white font-bold text-sm transition" data-i18n="hero_wa_cta">
            💬 محادثة واتساب مباشرة
          </a>'''
        portfolio_footer_contact = f'''<a href="https://wa.me/{clean_wa}" target="_blank" rel="noopener" class="hover:text-cyan-400 font-bold">📲 WhatsApp: {html.escape(whatsapp)}</a>'''
    else:
        portfolio_contact_cta = '''<span class="px-8 py-3.5 rounded-xl bg-slate-800 border border-slate-700 text-slate-300 font-bold text-sm" data-i18n="contact_pending">بيانات التواصل قيد الإعداد</span>'''
        portfolio_footer_contact = '''<span class="font-bold" data-i18n="contact_pending">بيانات التواصل قيد الإعداد</span>'''

    if not items:
        raw_items = get_default_catalog("portfolio", ctx_full)
        items = []
        for i, it in enumerate(raw_items):
            items.append({
                "id": i + 1,
                "title": it["title"],
                "title_en": it.get("title_en", it["title"]),
                "price": it["price"],
                "category": it["category"],
                "category_en": it.get("category_en", it["category"]),
                "badge": it.get("badge", ""),
                "badge_en": it.get("badge_en", it.get("badge", "")),
                "description": it["desc"],
                "desc_en": it.get("desc_en", it["desc"]),
            })
    else:
        normalized_items = []
        for i, it in enumerate(items):
            it_dict = dict(it)
            t_ar = str(it_dict.get("title") or f"خدمة {i+1}").strip()
            c_ar = str(it_dict.get("category") or ("تصميم واجهات وتجربة المستخدم" if track == "design" else ("استشارات ذكاء اصطناعي" if track == "ai" else ("تطوير برمجيات" if track == "dev" else "خدمات الفحص الأمني")))).strip()
            b_ar = str(it_dict.get("badge") or "").strip()
            d_ar = str(it_dict.get("description") or it_dict.get("desc") or "").strip()
            normalized_items.append({
                "id": i + 1,
                "title": t_ar,
                "title_en": str(it_dict.get("title_en") or t_ar).strip(),
                "price": _safe_price(it_dict.get("price")),
                "category": c_ar,
                "category_en": str(it_dict.get("category_en") or CATEGORY_TRANS.get(c_ar, c_ar)).strip(),
                "badge": b_ar,
                "badge_en": str(it_dict.get("badge_en") or BADGE_TRANS.get(b_ar, b_ar)).strip(),
                "description": d_ar,
                "desc_en": str(it_dict.get("desc_en") or d_ar).strip()
            })
        items = normalized_items

    # Track-specific configuration
    if track == "ai":
        track_icon = "🧠"
        default_slogan = "مهندس ذكاء اصطناعي وتطوير نماذج التعلم العميق والوكلاء المستقلين"
        default_slogan_en = "AI & Deep Learning Engineer • Autonomous Agents & LLM Systems"
        role_sub_ar = "مهندس ذكاء اصطناعي وتعلم عميق"
        role_sub_en = "AI & DEEP LEARNING ENGINEER"
        hero_tag_ar = "⚡ مهندس ذكاء اصطناعي • نماذج تعلم عميق ووكلاء أذكياء"
        hero_tag_en = "⚡ AI & DEEP LEARNING ENGINEER • AUTONOMOUS AGENTS"
        hero_desc_ar = "متخصص في بناء وتدريب نماذج التعلم العميق (Deep Learning)، وهندسة الوكلاء الأذكياء المستقلين (Autonomous AI Agents)، وتطبيقات الذكاء الاصطناعي التوليدي والـ LLMs ونشرها على البنى السحابية عالية الأداء."
        hero_desc_en = "Specializing in deep learning architectures, LLM systems, autonomous AI agent pipelines, and high-performance MLOps cloud deployments."
        cta_audit_ar = "🤖 اطلب استشارة أو بناء نظام AI"
        cta_audit_en = "🤖 Request AI System / Consultation"
        stat_1_val, stat_1_ar, stat_1_en = "+35", "نماذج ووكلاء منشورة", "AI Models & Agents"
        stat_2_val, stat_2_ar, stat_2_en = "99.4%", "دقة النماذج في الإنتاج", "Production Accuracy"
        stat_3_val, stat_3_ar, stat_3_en = "0", "أخطاء استدلال النماذج", "Inference Failures"
        stat_4_val, stat_4_ar, stat_4_en = "+5", "سنوات خبرة في الذكاء الاصطناعي", "Years AI Experience"
        skills_arsenal_tag = "AI ARSENAL & MLOPS"
        skills_title_ar = "المهارات والشهادات المعتمدة في الذكاء الاصطناعي"
        skills_title_en = "Verified AI Skills & Certifications"
        skill_1_icon = "🤖"
        skill_1_t_ar = "Autonomous Agents & LLMs"
        skill_1_t_en = "Autonomous Agents & LLMs"
        skill_1_d_ar = "بناء أنظمة وكلاء مستقلين، تكامل RAG، وهندسة الأوامر المتقدمة واستدعاء الأدوات وقواعد البيانات."
        skill_1_d_en = "Autonomous agent architectures, RAG pipelines, fine-tuning, and structured tool calling."
        skill_2_icon = "🧠"
        skill_2_t_ar = "Deep Learning & Vision/NLP"
        skill_2_t_en = "Deep Learning & Vision/NLP"
        skill_2_d_ar = "تدريب شبكات CNNs و Transformers و PyTorch على الرؤية الحاسوبية ومعالجة النصوص بدقة فائقة."
        skill_2_d_en = "Training Vision Transformers, PyTorch deep neural nets, and production NLP pipelines."
        skill_3_icon = "⚡"
        skill_3_t_ar = "MLOps & Scalable Inference"
        skill_3_t_en = "MLOps & Scalable Inference"
        skill_3_d_ar = "تسريع الاستدلال عبر TensorRT و Triton، ونشر النماذج عبر Docker و Kubernetes و Cloud APIs."
        skill_3_d_en = "Low-latency model serving with TensorRT, Triton, Docker containers, and Cloud APIs."
        certs = [
            ("🎖️ TensorFlow Certified Developer", "🎖️ TensorFlow Certified Developer"),
            ("🧠 PyTorch Deep Learning Specialist", "🧠 PyTorch Deep Learning Specialist"),
            ("⚡ AWS Machine Learning Specialty", "⚡ AWS Machine Learning Specialty"),
            ("🤖 NVIDIA Deep Learning Institute", "🤖 NVIDIA Deep Learning Institute"),
        ]
        projects_tag = "AI CASE STUDIES"
        projects_title_ar = "أبرز مشاريع وأنظمة الذكاء الاصطناعي"
        projects_title_en = "Featured AI Case Studies & Deployments"
        proj_1_tag = "AUTONOMOUS AGENTS"
        proj_1_t_ar = "منظومة وكلاء أذكياء متعددة المهام للمؤسسات"
        proj_1_t_en = "Enterprise Autonomous Multi-Agent Platform"
        proj_1_d_ar = "بناء منصة وكلاء ذاتية اتخاذ القرارات لأتمتة العمليات التجارية، التحليل التنبؤي، والتكامل الآمن مع قواعد البيانات والـ APIs."
        proj_1_d_en = "Designed and deployed an autonomous agent platform automating enterprise workflows and complex data synthesis."
        proj_1_b_ar = "✅ إنتاجية مضاعفة بنسبة 400% واستجابة فورية"
        proj_1_b_en = "✅ 400% Productivity Boost & Sub-Second Latency"
        proj_2_tag = "DEEP LEARNING VISION"
        proj_2_t_ar = "نظام فحص أمني وبصري فوري بالتعلم العميق"
        proj_2_t_en = "Real-Time Deep Learning Vision Inspection System"
        proj_2_d_ar = "تدريب نموذج Vision Transformer لتصنيف واكتشاف الأنماط والعيوب بدقة 99.4% في زمن استدلال أقل من 15ms في خطوط الإنتاج."
        proj_2_d_en = "Trained a custom Vision Transformer achieving 99.4% defect classification accuracy under 15ms latency."
        proj_2_b_ar = "✅ دقة استدلال 99.4% وتشغيل إنتاجي لحظي"
        proj_2_b_en = "✅ 99.4% Accuracy with Production-Grade Real-Time Inference"
        modal_hire_title_ar = "طلب استشارة أو بناء نظام ذكاء اصطناعي 🤖"
        modal_hire_title_en = "Request AI Advisory or System Development 🤖"
        modal_hire_sub_ar = "أدخل بياناتك وسيتم التواصل وتأكيد التعاقد فوراً"
        modal_hire_sub_en = "Submit your details for immediate technical onboarding and scoping."
    elif track == "dev":
        track_icon = "💻"
        default_slogan = "مهندس برمجيات وتطوير الحلول الرقمية المتكاملة والأنظمة السحابية"
        default_slogan_en = "Full-Stack Software Engineer & Distributed Cloud Systems Architect"
        role_sub_ar = "مهندس برمجيات وتطوير حلول سحابية"
        role_sub_en = "SOFTWARE ARCHITECT & CLOUD DEV"
        hero_tag_ar = "⚡ مهندس برمجيات • منصات سحابية وحلول متكاملة"
        hero_tag_en = "⚡ FULL-STACK SOFTWARE ARCHITECT & CLOUD DEVELOPER"
        hero_desc_ar = "متخصص في بناء المنصات السحابية المتكاملة، هندسة النظم الموزعة، تطوير واجهات المستخدم التفاعلية والـ APIs فائقة الأداء، وضمان أعلى معايير الجودة والأمان البرمجي."
        hero_desc_en = "Architecting robust web applications, high-performance distributed systems, modern frontend UIs, and resilient cloud architectures."
        cta_audit_ar = "💻 اطلب استشارة أو تطوير منصة"
        cta_audit_en = "💻 Request Platform Development"
        stat_1_val, stat_1_ar, stat_1_en = "+50", "تطبيق ومنصة منشورة", "Shipped Platforms"
        stat_2_val, stat_2_ar, stat_2_en = "99.9%", "جاهزية واستقرار الأنظمة", "System Uptime"
        stat_3_val, stat_3_ar, stat_3_en = "100%", "تغطية اختبارات الكود", "Test Coverage"
        stat_4_val, stat_4_ar, stat_4_en = "+6", "سنوات خبرة برمجية", "Years Dev Experience"
        skills_arsenal_tag = "DEV STACK & ARCHITECTURE"
        skills_title_ar = "المهارات والشهادات البرمجية المعتمدة"
        skills_title_en = "Verified Dev Skills & Certifications"
        skill_1_icon = "💻"
        skill_1_t_ar = "Full-Stack Web Development"
        skill_1_t_en = "Full-Stack Web Development"
        skill_1_d_ar = "تطوير الواجهات بـ React/Next.js وبناء خدمات الـ Backend المتقدمة بـ Python و Node.js و Go."
        skill_1_d_en = "Modern frontend with React/Next.js and scalable backend microservices with Python, Node.js, and Go."
        skill_2_icon = "☁️"
        skill_2_t_ar = "Cloud & DevOps CI/CD"
        skill_2_t_en = "Cloud & DevOps CI/CD"
        skill_2_d_ar = "إدارة البنى التحتية بـ Docker و Kubernetes، وأتمتة خطوط الاختبار والنشر المستمر CI/CD."
        skill_2_d_en = "Container orchestration with Docker & K8s, automated CI/CD pipelines, and cloud monitoring."
        skill_3_icon = "🗄️"
        skill_3_t_ar = "Database & System Architecture"
        skill_3_t_en = "Database & System Architecture"
        skill_3_d_ar = "تصميم قواعد البيانات العلائقية وتحسين استعلامات SQL وأداء التخزين المؤقت Redis."
        skill_3_d_en = "Schema design, query optimization for PostgreSQL/MySQL, and high-speed Redis caching."
        certs = [
            ("🎖️ AWS Certified Solutions Architect", "🎖️ AWS Certified Solutions Architect"),
            ("💻 Certified Kubernetes Administrator", "💻 Certified Kubernetes Administrator"),
            ("⚡ Professional Scrum Master", "⚡ Professional Scrum Master"),
            ("🚀 GitHub Certified Developer", "🚀 GitHub Certified Developer"),
        ]
        projects_tag = "ENGINEERING PROJECTS"
        projects_title_ar = "أبرز المنصات والأنظمة المنفذة"
        projects_title_en = "Featured Software Platforms & Engineering"
        proj_1_tag = "HIGH-SCALE SAAS"
        proj_1_t_ar = "تطوير منصة سحابية لإدارة المعاملات الضخمة"
        proj_1_t_en = "High-Scale Cloud Transaction Platform"
        proj_1_d_ar = "بناء بنية Microservices متقدمة تتحمل أكثر من 100,000 طلب في الدقيقة مع مزامنة لحظية لقواعد البيانات."
        proj_1_d_en = "Architected a high-concurrency microservices platform handling 100k+ requests/min with sub-20ms latency."
        proj_1_b_ar = "✅ معمارية مرنة بزمن استجابة أقل من 20ms"
        proj_1_b_en = "✅ High Availability & Sub-20ms Response Time"
        proj_2_tag = "FINTECH & COMMERCE"
        proj_2_t_ar = "بوابة دفع رقمية وتكامل بوابات التجارة الإلكترونية"
        proj_2_t_en = "FinTech Payment Gateway & Merchant Platform"
        proj_2_d_ar = "تطوير نظام دفع إلكتروني متكامل يدعم المحافظ الإلكترونية والمصادقة متعددة العوامل بحماية تامة."
        proj_2_d_en = "Engineered secure payment infrastructure with multi-tenant isolation, idempotency, and audit trails."
        proj_2_b_ar = "✅ نظام مؤمن بنسبة 100% ضد الأخطاء المزدوجة"
        proj_2_b_en = "✅ 100% Idempotent & Fault-Tolerant"
        modal_hire_title_ar = "طلب استشارة برمجية أو تطوير منصة 💻"
        modal_hire_title_en = "Request Software Advisory or Platform Engineering 💻"
        modal_hire_sub_ar = "أدخل بياناتك وسيتم التواصل وتأكيد التعاقد فوراً"
        modal_hire_sub_en = "Submit your requirements for swift architecture review and planning."
    elif track == "design":
        track_icon = "🎨"
        default_slogan = "مصمم واجهات وتجربة المستخدم وتطوير الأنظمة التصميمية الرقمية"
        default_slogan_en = "Lead UI/UX Product Designer & Design Systems Architect"
        role_sub_ar = "تصميم واجهات وتجربة المستخدم"
        role_sub_en = "LEAD UI/UX PRODUCT DESIGNER"
        hero_tag_ar = "⚡ مصمم واجهات وتجربة المستخدم • أنظمة تصميم وبروتوتايب"
        hero_tag_en = "⚡ LEAD UI/UX PRODUCT DESIGNER • DESIGN SYSTEMS"
        hero_desc_ar = "متخصص في تصميم تجارب المستخدم الرقمية السلسة والواجهات العصرية (UI/UX)، بناء أنظمة التصميم الشاملة (Design Systems) على Figma، وإجراء أبحاث المستخدمين لتحويل المنتجات المعقدة إلى تجارب تفاعلية ممتعة تضاعف معدلات التحويل."
        hero_desc_en = "Crafting intuitive digital experiences and sleek modern interfaces, architecting scalable design systems in Figma, and leading user research to turn complex software into high-converting products."
        cta_audit_ar = "🎨 اطلب استشارة أو تصميم منتج"
        cta_audit_en = "🎨 Request UI/UX Design / Audit"
        stat_1_val, stat_1_ar, stat_1_en = "+40", "تطبيق ومنتج مصمم", "Shipped UI/UX Projects"
        stat_2_val, stat_2_ar, stat_2_en = "98%", "رضا واختبارات المستخدمين", "User Usability Score"
        stat_3_val, stat_3_ar, stat_3_en = "3.2x", "مضاعفة معدل التحويل", "Conversion Multiplier"
        stat_4_val, stat_4_ar, stat_4_en = "+5", "سنوات خبرة في التصميم", "Years UX Experience"
        skills_arsenal_tag = "DESIGN ARSENAL & TOOLING"
        skills_title_ar = "المهارات والشهادات المعتمدة في الـ UI/UX"
        skills_title_en = "Verified UI/UX Skills & Certifications"
        skill_1_icon = "🎨"
        skill_1_t_ar = "UI/UX & Design Systems"
        skill_1_t_en = "UI/UX & Design Systems"
        skill_1_d_ar = "إتقان كامل لـ Figma، بناء مكتبات المكونات التفاعلية، ومطابقة معايير إمكانية الوصول والتسليم البرمجي."
        skill_1_d_en = "Mastery in Figma, scalable design tokens, WCAG accessibility, and pixel-perfect dev handoffs."
        skill_2_icon = "🔍"
        skill_2_t_ar = "User Research & Heuristic Audit"
        skill_2_t_en = "User Research & Heuristic Audit"
        skill_2_d_ar = "أبحاث سلوك المستخدمين، خرائط التعاطف، واختبارات القابلية لتحسين رحلة العميل وتقليل الاحتكاك."
        skill_2_d_en = "Behavioral user research, empathy mapping, usability testing, and frictionless journey optimization."
        skill_3_icon = "✨"
        skill_3_t_ar = "Interactive Prototyping & Motion"
        skill_3_t_en = "Interactive Prototyping & Motion"
        skill_3_d_ar = "بناء بروتوتايب تفاعلي متقدم يحاكي المنتج الحقيقي بحركات دقيقة وانتقالات سلسة."
        skill_3_d_en = "High-fidelity clickable prototypes with realistic states, micro-interactions, and smart animation."
        certs = [
            ("🎖️ Google Certified Professional UX Designer", "🎖️ Google Certified Professional UX Designer"),
            ("🎨 Nielsen Norman Group (NN/g) UX Master", "🎨 Nielsen Norman Group (NN/g) UX Master"),
            ("✨ Interaction Design Foundation (IxDF)", "✨ Interaction Design Foundation (IxDF)"),
            ("🚀 Figma Advanced Design Systems Specialist", "🚀 Figma Advanced Design Systems Specialist"),
        ]
        projects_tag = "DESIGN CASE STUDIES"
        projects_title_ar = "أبرز مشاريع وتجارب المستخدم المنفذة"
        projects_title_en = "Featured UI/UX Case Studies"
        proj_1_tag = "FINTECH MOBILE APP"
        proj_1_t_ar = "تصميم تطبيق مالي رقمي وسهل الاستخدام"
        proj_1_t_en = "FinTech Mobile Banking & Wallet App"
        proj_1_d_ar = "إعادة تصميم تجربة التحويلات المالية وإدارة البطاقات والمحافظ برحلة مستخدم فائقة البساطة رفعت نسبة الإكمال بـ 45%."
        proj_1_d_en = "End-to-end UX redesign for personal banking and digital wallet, reducing onboarding drop-off by 45%."
        proj_1_b_ar = "✅ زيادة معدل الإكمال 45% وتجربة خالية من التعقيد"
        proj_1_b_en = "✅ +45% Task Completion & Zero UX Friction"
        proj_2_tag = "ENTERPRISE SAAS DASHBOARD"
        proj_2_t_ar = "نظام تصميم ولوحة تحكم متطورة للمؤسسات"
        proj_2_t_en = "Enterprise B2B SaaS Dashboard & Design System"
        proj_2_d_ar = "بناء نظام تصميم متكامل بأكثر من 200 مكون تفاعلي مع لوحة بيانات ذكية متوافقة مع الوضعين الليلي والنهاري."
        proj_2_d_en = "Architected a design system with 200+ Figma components and a high-density data dashboard with full dark mode."
        proj_2_b_ar = "✅ 200+ مكون تفاعلي وتسريع دورة تطوير الواجهات 3x"
        proj_2_b_en = "✅ 200+ Components & 3x Accelerated Frontend Delivery"
        modal_hire_title_ar = "طلب استشارة تصميم أو مشروع UI/UX 🎨"
        modal_hire_title_en = "Request UI/UX Advisory or Project Design 🎨"
        modal_hire_sub_ar = "أدخل بياناتك وسيتم التواصل معك لمناقشة التفاصيل فوراً"
        modal_hire_sub_en = "Submit your product details for immediate design review and scoping."
    else:  # "cyber"
        track_icon = "🛡️"
        default_slogan = "خبير الأمن السيبراني واختبار الاختراق وتأمين الأنظمة السحابية"
        default_slogan_en = "Certified Cybersecurity Expert & Cloud Penetration Specialist"
        role_sub_ar = "أمن سيبراني وهندسة برمجيات"
        role_sub_en = "CYBERSECURITY & DEV"
        hero_tag_ar = "⚡ فريق أحمر وتأمين سحابي • هاكر أخلاقي معتمد"
        hero_tag_en = "⚡ RED TEAM & CLOUD DEFENDER • ETHICAL HACKER"
        hero_desc_ar = "متخصص في حماية أصول الشركات الرقمية، اختبار اختراق الويب وتطبيقات الهاتف، تحليل وكشف الثغرات الأمنية (Vulnerability Assessment)، وتأمين البنية التحتية السحابية لضمان استمرارية الأعمال بأمان تام."
        hero_desc_en = "Dedicated to safeguarding enterprise digital assets, web/mobile application penetration testing, vulnerability assessment, and cloud infrastructure hardening for zero-downtime resilience."
        cta_audit_ar = "🛡️ احجز فحصاً أمنياً لنظامك"
        cta_audit_en = "🛡️ Book Security Assessment"
        stat_1_val, stat_1_ar, stat_1_en = "+45", "فحص أمني ناجح", "Successful Audits"
        stat_2_val, stat_2_ar, stat_2_en = "100%", "كشف ومعالجة الثغرات", "Vulnerability Remediation"
        stat_3_val, stat_3_ar, stat_3_en = "0", "اختراقات بعد التأمين", "Post-Hardening Breaches"
        stat_4_val, stat_4_ar, stat_4_en = "+5", "سنوات خبرة متقدمة", "Years Experience"
        skills_arsenal_tag = "TECHNICAL ARSENAL"
        skills_title_ar = "المهارات والشهادات المعتمدة"
        skills_title_en = "Verified Skills & Certifications"
        skill_1_icon = "🔍"
        skill_1_t_ar = "Penetration Testing"
        skill_1_t_en = "Penetration Testing"
        skill_1_d_ar = "اختبار اختراق تطبيقات الويب (OWASP Top 10)، فحص الـ APIs، الهندسة العكسية، وتحليل حركة البيانات المشفرة."
        skill_1_d_en = "Web application testing (OWASP Top 10), API security assessments, reverse engineering, and encrypted traffic analysis."
        skill_2_icon = "☁️"
        skill_2_t_ar = "Cloud & Infra Hardening"
        skill_2_t_en = "Cloud & Infra Hardening"
        skill_2_d_ar = "تأمين خوادم لينكس والـ Docker، إدارة جدران الحماية، ضبط صلاحيات IAM، وحماية البنى السحابية في AWS و GCP."
        skill_2_d_en = "Hardening Linux & Docker hosts, firewall orchestration, fine-grained IAM policies across AWS & Google Cloud Platform."
        skill_3_icon = "🚨"
        skill_3_t_ar = "Incident Response"
        skill_3_t_en = "Incident Response"
        skill_3_d_ar = "التحقيق الجنائي الرقمي (DFIR)، تتبع الاختراقات، صد هجمات DDoS، وتحليل البرمجيات الخبيثة Malware Analysis."
        skill_3_d_en = "Digital forensics & incident response (DFIR), intrusion containment, DDoS mitigation, and advanced malware analysis."
        certs = [
            ("🎖️ OSCP Certified", "🎖️ OSCP Certified"),
            ("🛡️ CEH v12 (Ethical Hacker)", "🛡️ CEH v12 (Ethical Hacker)"),
            ("📜 CompTIA Security+", "📜 CompTIA Security+"),
            ("🔒 CISSP Candidate", "🔒 CISSP Candidate"),
        ]
        projects_tag = "SECURITY PORTFOLIO"
        projects_title_ar = "أبرز العمليات والمشاريع الأمنية"
        projects_title_en = "Featured Security Engagements"
        proj_1_tag = "FINTECH PENTEST"
        proj_1_t_ar = "تدقيق أمان منصة دفع ومحفظة رقمية"
        proj_1_t_en = "FinTech Payment Gateway & Wallet Security Audit"
        proj_1_d_ar = "إجراء فحص أمني شامل لبوابة دفع مالية مصرية، واكتشاف 6 ثغرات في منطق الأعمال (Business Logic) وتأمين تدفق عمليات السحب والتحويل."
        proj_1_d_en = "Conducted exhaustive pentesting for an Egyptian payment gateway; identified 6 critical business logic flaws and secured transfer flows."
        proj_1_b_ar = "✅ تم إغلاق جميع الثغرات وحصول العميل على شهادة امتثال"
        proj_1_b_en = "✅ 100% Remediation & Certified Compliance Achieved"
        proj_2_tag = "CLOUD SECURITY"
        proj_2_t_ar = "تأمين بنية تحتية سحابية لشركة كبرى"
        proj_2_t_en = "Enterprise Cloud Infrastructure Hardening"
        proj_2_d_ar = "إعادة هيكلة سياسات IAM وجدران الحماية، وعزل قواعد البيانات الحساسة خلف شبكات VPC خاصة مع تفعيل المراقبة اللحظية 24/7."
        proj_2_d_en = "Restructured IAM controls, isolated sensitive production databases behind isolated VPC subnets with 24/7 telemetry."
        proj_2_b_ar = "✅ منع محاولات الاختراق الخارجية بنسبة 100%"
        proj_2_b_en = "✅ 100% External Intrusion Prevention Rate"
        modal_hire_title_ar = "طلب استشارة أو فحص أمني 🛡️"
        modal_hire_title_en = "Request Advisory or Security Assessment 🛡️"
        modal_hire_sub_ar = "أدخل بياناتك وسيتم التواصل وتأكيد التعاقد فوراً"
        modal_hire_sub_en = "Submit your engagement details for immediate scheduling and onboarding."

    slogan = _safe_text(settings.get("slogan"), default_slogan, 500)
    items_json = _json_for_script(items)

    service_cards = []
    for it in items:
        t_raw = str(it.get("title") or "استشارة برمجية وأمنية")
        title = html.escape(t_raw)
        desc = html.escape(str(it.get("description") or "مراجعة معمارية وتدقيق متقدم للأكواد والأنظمة."))
        price = _safe_price(it.get("price"))
        price_display = f"{price:,.0f} ج.م" if price > 0 else "حسب نطاق المشروع"
        service_cards.append(f"""
        <div class="p-6 rounded-2xl bg-slate-900 border border-slate-800 hover:border-cyan-500 flex flex-col justify-between transition group hover:-translate-y-1">
          <div>
            <div class="w-10 h-10 rounded-xl bg-cyan-500/10 text-cyan-400 flex items-center justify-center text-xl mb-4">{track_icon}</div>
            <h4 class="font-bold text-white text-base mb-2 group-hover:text-cyan-400 transition">{title}</h4>
            <p class="text-xs text-slate-400 font-readex leading-relaxed mb-6">{desc}</p>
          </div>
          <div>
            <div class="text-xs text-slate-500 mb-2 font-mono">الاستثمار المتوقع: <span class="text-white font-bold">{price_display}</span></div>
            <button onclick="requestService({_inline_js_value(t_raw)}, {price})" class="w-full py-2.5 rounded-xl bg-cyan-500/20 hover:bg-cyan-500 text-cyan-300 hover:text-slate-950 border border-cyan-500/40 font-bold text-xs transition active:scale-95">
              طلب هذه الخدمة ➔
            </button>
          </div>
        </div>
        """)
    services_markup = "\n".join(service_cards)

    cert_badges_html = " ".join([
        f'<span class="px-4 py-2 rounded-xl bg-slate-900 border border-cyan-500/40 text-cyan-300 font-mono text-xs font-bold">{c[0]}</span>'
        for c in certs
    ])

    return f"""<!doctype html>
<html lang="ar" dir="rtl" class="scroll-smooth dark">
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
      darkMode: 'class',
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

    /* Light Mode Overrides for Portfolio */
    html.light body {{
      background-color: #f8fafc !important;
      color: #0f172a !important;
    }}
    html.light .bg-grid {{
      background-image: radial-gradient(rgba(15, 23, 42, 0.08) 1px, transparent 1px);
    }}
    html.light .bg-slate-950,
    html.light .bg-slate-950\/90,
    html.light .bg-slate-950\/80,
    html.light .bg-slate-950\/60 {{
      background-color: #ffffff !important;
      border-color: #e2e8f0 !important;
      color: #0f172a !important;
    }}
    html.light header {{
      background-color: rgba(255, 255, 255, 0.95) !important;
      border-color: #e2e8f0 !important;
    }}
    html.light .bg-slate-900,
    html.light .bg-slate-900\/90,
    html.light .bg-slate-900\/80,
    html.light .bg-slate-900\/60 {{
      background-color: #f1f5f9 !important;
      border-color: #cbd5e1 !important;
      color: #0f172a !important;
    }}
    html.light .text-white {{
      color: #0f172a !important;
    }}
    html.light .text-slate-300,
    html.light .text-slate-400 {{
      color: #475569 !important;
    }}
    html.light .border-slate-800,
    html.light .border-slate-700 {{
      border-color: #cbd5e1 !important;
    }}
    html.light input,
    html.light textarea {{
      background-color: #ffffff !important;
      border-color: #cbd5e1 !important;
      color: #0f172a !important;
    }}
    html.light #hire-modal > div {{
      background-color: #ffffff !important;
      color: #0f172a !important;
      border-color: #cbd5e1 !important;
    }}
  </style>
</head>
<body class="selection:bg-cyan-500 selection:text-black min-h-screen flex flex-col bg-grid">
  <a href="#main-content" class="sr-only focus:not-sr-only focus:fixed focus:top-3 focus:left-3 focus:z-[100] focus:rounded-lg focus:bg-white focus:px-4 focus:py-3 focus:text-slate-950">تخطي إلى المحتوى الرئيسي / Skip to main content</a>

  <!-- Top Status Bar -->
  <div class="bg-slate-950/90 border-b border-cyan-950/60 text-xs py-2 px-4 backdrop-blur">
    <div class="max-w-7xl mx-auto flex items-center justify-between">
      <div class="flex items-center gap-2">
        <span class="inline-block w-2.5 h-2.5 rounded-full bg-emerald-400 animate-pulse"></span>
        <span class="text-emerald-400 font-mono font-bold" data-i18n="port_status_text">STATUS: AVAILABLE FOR CONTRACT & FREELANCE</span>
      </div>
      <div class="flex items-center gap-3">
        <div class="flex items-center gap-2">
          <button onclick="togglePortfolioTheme()" class="px-2 py-0.5 rounded-lg bg-slate-900 border border-slate-700 text-amber-400 font-mono text-[11px] font-bold transition hover:bg-slate-800" id="port-theme-btn">
            <span id="port-theme-icon">🌙</span> <span id="port-theme-lbl" data-i18n="theme_dark">ليلي</span>
          </button>
          <button onclick="togglePortfolioLang()" class="px-2 py-0.5 rounded-lg bg-slate-900 border border-slate-700 text-cyan-400 font-mono text-[11px] font-bold transition hover:bg-slate-800" id="port-lang-btn" data-i18n="lang_btn">
            English
          </button>
        </div>
        <div class="hidden sm:flex items-center gap-4 text-slate-400 font-mono text-[11px]">
          <span data-i18n="port_location">LOCATION: CAIRO, EG</span>
          <span>OS: LINUX / SEC</span>
        </div>
      </div>
    </div>
  </div>

  <!-- Header -->
  <header class="sticky top-0 z-40 bg-slate-950/80 backdrop-blur border-b border-slate-800">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-20 flex items-center justify-between">
      <div class="flex items-center gap-3">
        <div class="w-11 h-11 rounded-xl bg-cyan-500/10 border border-cyan-500/30 flex items-center justify-center text-xl text-cyan-400 shadow-md">
          {track_icon}
        </div>
        <div>
          <h1 class="text-lg sm:text-xl font-black text-white tracking-wide" data-i18n="brand_title">{html.escape(brand_name)}</h1>
          <p class="text-xs text-cyan-400 font-mono" data-i18n="port_role_sub">{role_sub_en}</p>
        </div>
      </div>

      <nav class="hidden md:flex items-center gap-8 text-sm font-bold text-slate-300">
        <a href="#about" class="hover:text-cyan-400 transition" data-i18n="port_nav_about">عن الخبير</a>
        <a href="#skills" class="hover:text-cyan-400 transition" data-i18n="port_nav_skills">المهارات والشهادات</a>
        <a href="#projects" class="hover:text-cyan-400 transition" data-i18n="port_nav_projects">المشاريع المنفذة</a>
        <a href="#services" class="hover:text-cyan-400 transition" data-i18n="port_nav_services">الخدمات والأسعار</a>
        <a href="#contact" class="hover:text-cyan-400 transition" data-i18n="port_nav_contact">تواصل معي</a>
      </nav>

      <div class="flex items-center gap-3">
        <button onclick="openHireModal()" class="px-5 py-2.5 rounded-xl font-black text-xs sm:text-sm bg-cyan-500 hover:bg-cyan-400 text-slate-950 transition shadow-lg shadow-cyan-500/20 active:scale-95" data-i18n="port_hire_btn">
          💼 طلب استشارة / توظيف
        </button>
      </div>
    </div>
  </header>

  <main id="main-content" tabindex="-1">
  <!-- Hero Section -->
  <section class="py-16 sm:py-24 relative overflow-hidden" id="about">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center relative z-10">
      <div class="inline-flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-mono font-bold bg-cyan-950/60 border border-cyan-500/30 text-cyan-300 mb-6">
        <span data-i18n="port_hero_tag">{hero_tag_ar}</span>
      </div>

      <h2 class="text-3xl sm:text-5xl lg:text-6xl font-black text-white leading-tight max-w-4xl mx-auto mb-6" data-i18n="port_hero_headline">
        {html.escape(slogan)}
      </h2>

      <p class="text-base sm:text-lg text-slate-300 max-w-2xl mx-auto font-readex leading-relaxed mb-10" data-i18n="port_hero_desc">
        {hero_desc_ar}
      </p>

      <div class="flex flex-wrap items-center justify-center gap-4">
        <button onclick="openHireModal()" class="px-8 py-3.5 rounded-xl bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-black text-sm shadow-xl shadow-cyan-500/25 transition hover:scale-105 active:scale-95" data-i18n="port_cta_audit">
          {cta_audit_ar}
        </button>
        {portfolio_contact_cta}
      </div>

      <!-- Stats Bar -->
      <div class="grid grid-cols-2 sm:grid-cols-4 gap-4 max-w-4xl mx-auto mt-16 pt-8 border-t border-slate-800/80">
        <div class="p-4 rounded-2xl bg-slate-900/60 border border-slate-800">
          <div class="text-2xl sm:text-3xl font-black text-cyan-400 font-mono">{stat_1_val}</div>
          <div class="text-xs text-slate-400 font-readex mt-1" data-i18n="stat_1">{stat_1_ar}</div>
        </div>
        <div class="p-4 rounded-2xl bg-slate-900/60 border border-slate-800">
          <div class="text-2xl sm:text-3xl font-black text-emerald-400 font-mono">{stat_2_val}</div>
          <div class="text-xs text-slate-400 font-readex mt-1" data-i18n="stat_2">{stat_2_ar}</div>
        </div>
        <div class="p-4 rounded-2xl bg-slate-900/60 border border-slate-800">
          <div class="text-2xl sm:text-3xl font-black text-amber-400 font-mono">{stat_3_val}</div>
          <div class="text-xs text-slate-400 font-readex mt-1" data-i18n="stat_3">{stat_3_ar}</div>
        </div>
        <div class="p-4 rounded-2xl bg-slate-900/60 border border-slate-800">
          <div class="text-2xl sm:text-3xl font-black text-purple-400 font-mono">{stat_4_val}</div>
          <div class="text-xs text-slate-400 font-readex mt-1" data-i18n="stat_4">{stat_4_ar}</div>
        </div>
      </div>
    </div>
  </section>

  <!-- Skills & Certifications Section -->
  <section id="skills" class="py-16 bg-slate-950/60 border-y border-slate-800">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <div class="text-center mb-12">
        <span class="text-xs font-mono font-bold text-cyan-400 tracking-wider">{skills_arsenal_tag}</span>
        <h3 class="text-2xl sm:text-3xl font-black text-white mt-1" data-i18n="skills_title">{skills_title_ar}</h3>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12">
        <div class="p-6 rounded-2xl bg-slate-900/90 border border-slate-800 hover:border-cyan-500/50 transition">
          <div class="text-3xl mb-3">{skill_1_icon}</div>
          <h4 class="font-bold text-lg text-white mb-2" data-i18n="skill_1_title">{skill_1_t_ar}</h4>
          <p class="text-xs text-slate-400 font-readex leading-relaxed" data-i18n="skill_1_desc">
            {skill_1_d_ar}
          </p>
        </div>
        <div class="p-6 rounded-2xl bg-slate-900/90 border border-slate-800 hover:border-cyan-500/50 transition">
          <div class="text-3xl mb-3">{skill_2_icon}</div>
          <h4 class="font-bold text-lg text-white mb-2" data-i18n="skill_2_title">{skill_2_t_ar}</h4>
          <p class="text-xs text-slate-400 font-readex leading-relaxed" data-i18n="skill_2_desc">
            {skill_2_d_ar}
          </p>
        </div>
        <div class="p-6 rounded-2xl bg-slate-900/90 border border-slate-800 hover:border-cyan-500/50 transition">
          <div class="text-3xl mb-3">{skill_3_icon}</div>
          <h4 class="font-bold text-lg text-white mb-2" data-i18n="skill_3_title">{skill_3_t_ar}</h4>
          <p class="text-xs text-slate-400 font-readex leading-relaxed" data-i18n="skill_3_desc">
            {skill_3_d_ar}
          </p>
        </div>
      </div>

      <!-- Certifications Badges -->
      <div class="flex flex-wrap items-center justify-center gap-3">
        {cert_badges_html}
      </div>
    </div>
  </section>

  <!-- Featured Projects Showcase -->
  <section id="projects" class="py-16 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
    <div class="text-center mb-12">
      <span class="text-xs font-mono font-bold text-cyan-400 tracking-wider">{projects_tag}</span>
      <h3 class="text-2xl sm:text-3xl font-black text-white mt-1" data-i18n="projects_title">{projects_title_ar}</h3>
    </div>

    <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
      <div class="p-6 rounded-2xl bg-slate-900/80 border border-slate-800 hover:border-cyan-500 transition">
        <div class="flex items-center justify-between mb-3">
          <span class="px-3 py-1 rounded-full text-[11px] font-mono font-bold bg-cyan-500/20 text-cyan-300">{proj_1_tag}</span>
          <span class="text-xs text-slate-400 font-mono">2026</span>
        </div>
        <h4 class="text-lg font-black text-white mb-2" data-i18n="proj_1_title">{proj_1_t_ar}</h4>
        <p class="text-xs text-slate-300 font-readex leading-relaxed mb-4" data-i18n="proj_1_desc">
          {proj_1_d_ar}
        </p>
        <span class="text-xs text-emerald-400 font-bold" data-i18n="proj_1_badge">{proj_1_b_ar}</span>
      </div>

      <div class="p-6 rounded-2xl bg-slate-900/80 border border-slate-800 hover:border-cyan-500 transition">
        <div class="flex items-center justify-between mb-3">
          <span class="px-3 py-1 rounded-full text-[11px] font-mono font-bold bg-purple-500/20 text-purple-300">{proj_2_tag}</span>
          <span class="text-xs text-slate-400 font-mono">2026</span>
        </div>
        <h4 class="text-lg font-black text-white mb-2" data-i18n="proj_2_title">{proj_2_t_ar}</h4>
        <p class="text-xs text-slate-300 font-readex leading-relaxed mb-4" data-i18n="proj_2_desc">
          {proj_2_d_ar}
        </p>
        <span class="text-xs text-emerald-400 font-bold" data-i18n="proj_2_badge">{proj_2_b_ar}</span>
      </div>
    </div>
  </section>

  <!-- Services & Rates Section -->
  <section id="services" class="py-16 bg-slate-950/80 border-t border-slate-800">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <div class="text-center mb-12">
        <span class="text-xs font-mono font-bold text-cyan-400 tracking-wider">SERVICES & CONTRACTS</span>
        <h3 class="text-2xl sm:text-3xl font-black text-white mt-1" data-i18n="services_title">باقات الخدمات والتعاقد الفوري</h3>
      </div>

      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6" id="portfolio-services-grid">
        {services_markup}
      </div>
    </div>
  </section>

  <!-- Contact & Footer -->
  </main>
  <footer id="contact" class="py-12 bg-slate-950 border-t border-slate-900 text-xs">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between gap-6">
      <div>
        <p class="font-bold text-white text-sm mb-1" data-i18n="brand_title">{html.escape(brand_name)}</p>
        <p class="text-slate-500 font-readex" data-i18n="port_footer_rights">جميع الحقوق محفوظة © 2026 — مصمم ومنشور عبر وكالة AutoCorp الذاتية</p>
      </div>
      <div class="flex items-center gap-4 text-slate-300">
        {portfolio_footer_contact}
        {f'''<span>•</span><a href="tel:{phone}" class="hover:text-cyan-400 font-bold">📞 {html.escape(phone)}</a>''' if phone else ''}
      </div>
    </div>
  </footer>

  <!-- Hire & Booking Modal -->
  <div id="hire-modal" class="modal-backdrop hidden fixed inset-0 bg-slate-950/80 backdrop-blur z-50 flex items-center justify-center p-4">
    <div class="bg-slate-900 border border-slate-800 rounded-3xl max-w-lg w-full p-6 sm:p-8 shadow-2xl relative text-right">
      <div class="flex items-center justify-between pb-4 mb-4 border-b border-slate-800">
        <div>
          <h3 class="text-lg font-black text-white" data-i18n="modal_hire_title">{modal_hire_title_ar}</h3>
          <p class="text-xs text-slate-400 font-readex" data-i18n="modal_hire_sub">{modal_hire_sub_ar}</p>
        </div>
        <button onclick="closeHireModal()" class="w-8 h-8 rounded-full bg-slate-800 text-slate-400 hover:text-white flex items-center justify-center font-bold">✕</button>
      </div>

      <form id="hire-form" onsubmit="submitHireRequest(event)" class="space-y-4">
        <div>
          <label class="block text-xs font-bold text-slate-300 mb-1" data-i18n="lbl_name">الاسم أو اسم المؤسسة *</label>
          <input type="text" id="h-name" required placeholder="مثال: م. أحمد عبد الله" class="w-full px-3.5 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-white text-sm focus:outline-none focus:border-cyan-500">
        </div>
        <div>
          <label class="block text-xs font-bold text-slate-300 mb-1" data-i18n="lbl_phone">رقم الهاتف / واتساب *</label>
          <input type="tel" id="h-phone" required placeholder="مثال: 01012345678" class="w-full px-3.5 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-white text-sm focus:outline-none focus:border-cyan-500">
        </div>
        <div>
          <label class="block text-xs font-bold text-slate-300 mb-1" data-i18n="lbl_service">الخدمة المطلوبة *</label>
          <input type="text" id="h-service" required placeholder="مثال: استشارة وتطوير نظام ذكاء اصطناعي" class="w-full px-3.5 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-white text-sm focus:outline-none focus:border-cyan-500">
        </div>
        <div>
          <label class="block text-xs font-bold text-slate-300 mb-1" data-i18n="lbl_scope">تفاصيل النطاق / الهدف المطلوب *</label>
          <textarea id="h-scope" required placeholder="وصف المشروع، الأنظمة المطلوبة، ونطاق التنفيذ" rows="2" class="w-full px-3.5 py-2 rounded-xl bg-slate-950 border border-slate-800 text-white text-sm focus:outline-none focus:border-cyan-500"></textarea>
        </div>

        <button type="submit" id="h-submit-btn" class="w-full py-3.5 rounded-xl font-black text-slate-950 bg-cyan-500 hover:bg-cyan-400 text-sm shadow-lg shadow-cyan-500/25 transition" data-i18n="btn_submit_hire">
          🚀 إرسال طلب التعاقد الآن
        </button>
      </form>
    </div>
  </div>

  <script>
    const SITE_JOB_ID = {job_id};
    const WA_NUMBER = '{clean_wa}';
    const PORTFOLIO_SERVICES = {items_json};
    let selectedServiceName = '';
    let selectedServicePrice = 0;

    let portLang = 'ar';
    let isPortDark = true;

    const PORT_I18N = {{
      ar: {{
        port_status_text: 'STATUS: AVAILABLE FOR CONTRACT & FREELANCE',
        theme_dark: 'ليلي',
        theme_light: 'نهاري',
        lang_btn: 'English',
        port_location: 'LOCATION: CAIRO, EG',
        port_role_sub: '{role_sub_en}',
        port_nav_about: 'عن الخبير',
        port_nav_skills: 'المهارات والشهادات',
        port_nav_projects: 'المشاريع المنفذة',
        port_nav_services: 'الخدمات والأسعار',
        port_nav_contact: 'تواصل معي',
        port_hire_btn: '💼 طلب استشارة / توظيف',
        port_hero_tag: '{hero_tag_ar}',
        port_hero_headline: {_json_for_script(slogan)},
        port_hero_desc: '{hero_desc_ar}',
        port_cta_audit: '{cta_audit_ar}',
        hero_wa_cta: '💬 محادثة واتساب مباشرة',
        contact_pending: 'بيانات التواصل قيد الإعداد',
        stat_1: '{stat_1_ar}',
        stat_2: '{stat_2_ar}',
        stat_3: '{stat_3_ar}',
        stat_4: '{stat_4_ar}',
        skills_title: '{skills_title_ar}',
        skill_1_title: '{skill_1_t_ar}',
        skill_1_desc: '{skill_1_d_ar}',
        skill_2_title: '{skill_2_t_ar}',
        skill_2_desc: '{skill_2_d_ar}',
        skill_3_title: '{skill_3_t_ar}',
        skill_3_desc: '{skill_3_d_ar}',
        projects_title: '{projects_title_ar}',
        proj_1_title: '{proj_1_t_ar}',
        proj_1_desc: '{proj_1_d_ar}',
        proj_1_badge: '{proj_1_b_ar}',
        proj_2_title: '{proj_2_t_ar}',
        proj_2_desc: '{proj_2_d_ar}',
        proj_2_badge: '{proj_2_b_ar}',
        services_title: 'باقات الخدمات والتعاقد الفوري',
        btn_request_contract: '🛡️ طلب الخدمة والتعاقد',
        rate_expected: 'الاستثمار المتوقع:',
        currency: 'ج.م',
        port_footer_rights: 'جميع الحقوق محفوظة © 2026 — مصمم ومنشور عبر وكالة AutoCorp الذاتية',
        modal_hire_title: '{modal_hire_title_ar}',
        modal_hire_sub: '{modal_hire_sub_ar}',
        lbl_name: 'الاسم أو اسم المؤسسة *',
        lbl_phone: 'رقم الهاتف / واتساب *',
        lbl_service: 'الخدمة المطلوبة *',
        lbl_scope: 'تفاصيل النطاق / الهدف المطلوب *',
        btn_submit_hire: '🚀 إرسال طلب التعاقد الآن'
      }},
      en: {{
        port_status_text: 'STATUS: AVAILABLE FOR CONTRACT & FREELANCE',
        theme_dark: 'Dark',
        theme_light: 'Light',
        lang_btn: 'العربية',
        port_location: 'LOCATION: CAIRO, EG',
        port_role_sub: '{role_sub_en}',
        port_nav_about: 'About',
        port_nav_skills: 'Skills & Certs',
        port_nav_projects: 'Projects',
        port_nav_services: 'Services & Rates',
        port_nav_contact: 'Contact',
        port_hire_btn: '💼 Request Advisory / Hire',
        port_hero_tag: '{hero_tag_en}',
        port_hero_headline: '{default_slogan_en}',
        port_hero_desc: '{hero_desc_en}',
        port_cta_audit: '{cta_audit_en}',
        hero_wa_cta: '💬 Direct WhatsApp Chat',
        contact_pending: 'Contact Info In Progress',
        stat_1: '{stat_1_en}',
        stat_2: '{stat_2_en}',
        stat_3: '{stat_3_en}',
        stat_4: '{stat_4_en}',
        skills_title: '{skills_title_en}',
        skill_1_title: '{skill_1_t_en}',
        skill_1_desc: '{skill_1_d_en}',
        skill_2_title: '{skill_2_t_en}',
        skill_2_desc: '{skill_2_d_en}',
        skill_3_title: '{skill_3_t_en}',
        skill_3_desc: '{skill_3_d_en}',
        projects_title: '{projects_title_en}',
        proj_1_title: '{proj_1_t_en}',
        proj_1_desc: '{proj_1_d_en}',
        proj_1_badge: '{proj_1_b_en}',
        proj_2_title: '{proj_2_t_en}',
        proj_2_desc: '{proj_2_d_en}',
        proj_2_badge: '{proj_2_b_en}',
        services_title: 'Service Packages & Contracts',
        btn_request_contract: '🛡️ Request Service & Contract',
        rate_expected: 'Estimated Investment:',
        currency: 'EGP',
        port_footer_rights: 'All rights reserved © 2026 — Designed & deployed autonomously by AutoCorp AI',
        modal_hire_title: '{modal_hire_title_en}',
        modal_hire_sub: '{modal_hire_sub_en}',
        lbl_name: 'Your Name or Organization *',
        lbl_phone: 'Phone / WhatsApp *',
        lbl_service: 'Target Service *',
        lbl_scope: 'Assessment Scope & Asset Details *',
        btn_submit_hire: '🚀 Submit Contract Request Now'
      }}
    }};

    function escapeHtml(val) {{
      return String(val ?? '').replace(/[&<>"']/g, c => ({{ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }}[c]));
    }}

    function renderPortfolioServices() {{
      const grid = document.getElementById('portfolio-services-grid');
      if (!grid) return;
      const isEn = (portLang === 'en');
      const dict = PORT_I18N[portLang] || PORT_I18N.ar;
      grid.innerHTML = PORTFOLIO_SERVICES.map((it, idx) => {{
        const title = escapeHtml(isEn && it.title_en ? it.title_en : it.title);
        const cat = escapeHtml(isEn && it.category_en ? it.category_en : (it.category || 'Service'));
        const badge = escapeHtml(isEn && it.badge_en ? it.badge_en : (it.badge || 'Recommended'));
        const desc = escapeHtml(isEn && it.desc_en ? it.desc_en : (it.description || 'Specialized professional service.'));
        const price = Number(it.price) || 0;
        const priceDisplay = price > 0 ? (price.toLocaleString() + ' ' + dict.currency) : (isEn ? 'Per project scope' : 'حسب نطاق المشروع');
        return `
          <div class="p-6 rounded-2xl bg-slate-900 border border-slate-800 hover:border-cyan-500 flex flex-col justify-between transition group hover:-translate-y-1">
            <div>
              <div class="flex items-center justify-between mb-3">
                <span class="text-xs font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-300 font-bold">${{badge}}</span>
                <span class="text-xs text-cyan-400 font-mono">${{cat}}</span>
              </div>
              <h4 class="font-bold text-white text-base mb-2 group-hover:text-cyan-400 transition">${{title}}</h4>
              <p class="text-xs text-slate-400 font-readex leading-relaxed mb-6">${{desc}}</p>
            </div>
            <div>
              <div class="text-xs text-slate-500 mb-2 font-mono">${{dict.rate_expected}} <span class="text-white font-bold">${{priceDisplay}}</span></div>
              <button onclick="requestServiceByIndex(\${{idx}})" class="w-full py-2.5 rounded-xl bg-cyan-500/20 hover:bg-cyan-500 text-cyan-300 hover:text-slate-950 border border-cyan-500/40 font-bold text-xs transition active:scale-95">
                ${{dict.btn_request_contract}}
              </button>
            </div>
          </div>
        `;
      }}).join('');
    }}

    function requestServiceByIndex(idx) {{
      const it = PORTFOLIO_SERVICES[idx];
      if (!it) return;
      const isEn = (portLang === 'en');
      const title = isEn && it.title_en ? it.title_en : it.title;
      requestService(title, it.price || 0);
    }}

    function applyPortfolioTheme(dark) {{
      isPortDark = !!dark;
      if (isPortDark) {{
        document.documentElement.classList.add('dark');
        document.documentElement.classList.remove('light');
      }} else {{
        document.documentElement.classList.remove('dark');
        document.documentElement.classList.add('light');
      }}
      try {{ localStorage.setItem('portfolio_theme', isPortDark ? 'dark' : 'light'); }} catch(e) {{}}
      const icon = document.getElementById('port-theme-icon');
      const lbl = document.getElementById('port-theme-lbl');
      const dict = PORT_I18N[portLang] || PORT_I18N.ar;
      if (icon) icon.textContent = isPortDark ? '🌙' : '☀️';
      if (lbl) lbl.textContent = isPortDark ? dict.theme_dark : dict.theme_light;
    }}

    function togglePortfolioTheme() {{
      applyPortfolioTheme(!isPortDark);
    }}

    function applyPortfolioLang(lang) {{
      portLang = (lang === 'en') ? 'en' : 'ar';
      document.documentElement.lang = portLang;
      document.documentElement.dir = (portLang === 'ar') ? 'rtl' : 'ltr';
      try {{ localStorage.setItem('portfolio_lang', portLang); }} catch(e) {{}}

      const dict = PORT_I18N[portLang] || PORT_I18N.ar;
      const btn = document.getElementById('port-lang-btn');
      if (btn) btn.textContent = dict.lang_btn;

      const themeLbl = document.getElementById('port-theme-lbl');
      if (themeLbl) themeLbl.textContent = isPortDark ? dict.theme_dark : dict.theme_light;

      document.querySelectorAll('[data-i18n]').forEach(el => {{
        const key = el.getAttribute('data-i18n');
        if (dict[key]) {{
          if (el.tagName === 'INPUT' || el.tagName === 'TEXTAREA') {{
            el.placeholder = dict[key];
          }} else {{
            el.innerHTML = dict[key];
          }}
        }}
      }});

      renderPortfolioServices();
    }}

    function togglePortfolioLang() {{
      applyPortfolioLang(portLang === 'ar' ? 'en' : 'ar');
    }}

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
      btn.textContent = (portLang === 'en') ? '⏳ Submitting Request...' : '⏳ جاري إرسال الطلب...';

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
          headers: {{ 'Content-Type': 'application/json', 'Idempotency-Key': crypto.randomUUID() }},
          body: JSON.stringify(payload)
        }});
        const d = await res.json().catch(() => ({{}}));
        if (!res.ok) throw new Error(d.detail || 'Unable to submit the service request.');
        closeHireModal();
        const msg = encodeURIComponent(`مرحباً {html.escape(brand_name)} 👋\nأود التعاقد على خدمة: ${{payload.items[0].title}}\nالاسم: ${{payload.customer_name}}\nالهاتف: ${{payload.customer_phone}}`);
        if (WA_NUMBER) {{
          alert((portLang === 'en') ? '✅ Request received successfully! Opening WhatsApp for instant confirmation.' : '✅ تم استلام طلبك بنجاح! سيتم فتح واتساب للتأكيد المباشر.');
          window.open(`https://wa.me/${{WA_NUMBER}}?text=${{msg}}`, '_blank', 'noopener');
        }} else {{
          alert((portLang === 'en') ? '✅ Request received successfully.' : '✅ تم استلام طلبك بنجاح. بيانات التواصل قيد الإعداد.');
        }}
      }} catch(err) {{
        alert((portLang === 'en') ? 'Failed to submit request. Please try again.' : 'تعذر إرسال الطلب. يرجى المحاولة مرة أخرى.');
      }} finally {{
        btn.disabled = false;
        btn.textContent = (portLang === 'en') ? '🚀 Submit Contract Request Now' : '🚀 إرسال طلب التعاقد الآن';
      }}
    }}

    window.addEventListener('DOMContentLoaded', () => {{
      let savedTheme = 'dark';
      try {{ savedTheme = localStorage.getItem('portfolio_theme') || 'dark'; }} catch(e) {{}}
      applyPortfolioTheme(savedTheme === 'dark');

      let savedLang = 'ar';
      try {{ savedLang = localStorage.getItem('portfolio_lang') || 'ar'; }} catch(e) {{}}
      applyPortfolioLang(savedLang);
    }});
  </script>
</body>
</html>"""


def build_store_html(job_id: int, client: str, request: str, settings: dict, items: list, niche: str) -> str:
    """Generates the full-stack Arabic/English E-Commerce / Business SPA with dark/light mode."""
    brand_name = _safe_text(settings.get("brand_name") or client, (
        "معرض السيارات الكهربائية | إلكتريك درايف" if niche == "automotive"
        else "دار العود | متجر العطور الفاخرة" if niche == "perfumes"
        else "غاليري الأثاث والديكور العصري" if niche == "furniture"
        else "مكتبة دار المعرفة للكتب" if niche == "books"
        else "تيتانيوم فيتنس للمكملات والأجهزة" if niche == "gym"
        else "بت لاند لمستلزمات الحيوانات الأليفة" if niche == "pets"
        else "مناحل الشفاء للعسل الطبيعي" if niche == "honey"
        else "متجر الخضار الطازج" if niche == "vegetables"
        else "مطعم ومشويات كبابجي الأصيل" if niche == "restaurant"
        else "تكنو زون للأجهزة والإلكترونيات" if niche == "electronics"
        else "بوتيك الأناقة للملابس" if niche == "fashion"
        else "المتجر الإلكتروني المصري"
    ), 120)
    if brand_name.startswith("tg:"):
        brand_name = (
            "معرض أوتو إليكتريك للسيارات" if niche == "automotive"
            else "متجر العطور الفاخرة" if niche == "perfumes"
            else "معرض الأثاث الحديث" if niche == "furniture"
            else "مكتبة المعرفة للكتب" if niche == "books"
            else "متجر تيتانيوم فيتنس" if niche == "gym"
            else "متجر بت لاند" if niche == "pets"
            else "مناحل الشفاء للعسل الطبيعي" if niche == "honey"
            else "متجر الخضار الطازج" if niche == "vegetables"
            else "مطعم ومشويات الأصيل" if niche == "restaurant"
            else "تكنو زون للإلكترونيات" if niche == "electronics"
            else "بوتيك الموضة والأزياء" if niche == "fashion"
            else "المتجر الإلكتروني"
        )

    slogan = _safe_text(settings.get("slogan"), (
        "أحدث السيارات الكهربائية الفاخرة وشواحن الـ EV الذكية بأعلى معايير الأمان" if niche == "automotive"
        else "أفخم العطور الشرقية والفرنسية والزيوت العطرية النقية بثبات يدوم طويلاً" if niche == "perfumes"
        else "أرقى تصميمات الأثاث المنزلي والمكتبي العصري بأعلى جودة تصنيع" if niche == "furniture"
        else "عالم متكامل من أمهات الكتب والروايات ومصادر المعرفة بين يديك" if niche == "books"
        else "أقوى المكملات الغذائية الأصلية والأجهزة الرياضية الاحترافية لبناء جسمك المثالي" if niche == "gym"
        else "أفضل أغذية ومستلزمات ورعاية الحيوانات الأليفة بتوصيل سريع لباب بيتك" if niche == "pets"
        else "عسل سدر جبلي وطبيعي 100% مفحوص معملياً من المنحل لباب بيتك" if niche == "honey"
        else "خضارك طازج من المزرعة لباب بيتك بأعلى جودة وأفضل سعر في مصر" if niche == "vegetables"
        else "أشهى المأكولات والمشويات على أصولها بتوصيل سريع وساخن" if niche == "restaurant"
        else "أحدث الأجهزة والإلكترونيات الذكية بأفضل الأسعار وضمان حقيقي" if niche == "electronics"
        else "أحدث صيحات الموضة والأزياء الفاخرة بأقمشة ممتازة وتصميمات عصرية" if niche == "fashion"
        else "خدمات احترافية متكاملة تلبي كافة احتياجاتك بأعلى معايير الجودة"
    ), 500)

    slogan_en = (
        "Premium Electric Vehicles & Smart Home EV Chargers with Certified Warranty" if niche == "automotive"
        else "Finest Oriental & French Perfumes and Pure Fragrant Essential Oils" if niche == "perfumes"
        else "Modern Home & Office Furniture Crafted with Premium Quality Materials" if niche == "furniture"
        else "Comprehensive Collection of Literature, Bestsellers & Tech Masterpieces" if niche == "books"
        else "High-Grade Sports Nutrition, Supplements & Fitness Gear for Peak Performance" if niche == "gym"
        else "Premium Pet Nutrition, Accessories & Care Essentials Delivered Fast" if niche == "pets"
        else "100% Pure Natural Sidr Mountain Honey Tested from the Hive to Your Door" if niche == "honey"
        else "Fresh Farm Produce Delivered Directly to Your Doorstep Across Egypt" if niche == "vegetables"
        else "Authentic Charcoal Grills & Egyptian Dining Delivered Hot & Fast" if niche == "restaurant"
        else "Latest Smart Electronics, Gadgets & Accessories with Real Warranty" if niche == "electronics"
        else "Contemporary Fashion & Apparel Crafted with Egyptian Cotton Excellence" if niche == "fashion"
        else "Comprehensive Professional Services Delivered to the Highest Standards"
    )

    pal_key = settings.get("palette") or (
        "automotive" if niche == "automotive"
        else "perfumes" if niche == "perfumes"
        else "furniture" if niche == "furniture"
        else "books" if niche == "books"
        else "gym" if niche == "gym"
        else "pets" if niche == "pets"
        else "amber" if niche == "honey"
        else "emerald" if niche == "vegetables"
        else "sunset" if niche == "restaurant"
        else "teal" if niche == "clinic"
        else "indigo" if niche == "agency"
        else "crimson" if niche == "fashion"
        else "ocean" if niche == "electronics"
        else "ocean"
    )
    pal = PALETTES.get(pal_key, PALETTES["emerald"])
    primary = _safe_hex_color(settings.get("color_primary"), pal["primary"])
    secondary = _safe_hex_color(settings.get("color_secondary"), pal["secondary"])
    accent = pal["accent"]
    hero_grad = pal["hero_gradient"]

    phone = _safe_phone(settings.get("phone"))
    whatsapp = _safe_phone(settings.get("whatsapp"), phone)
    clean_wa = re.sub(r"[^\d]", "", whatsapp)
    if clean_wa.startswith("01"):
        clean_wa = "2" + clean_wa
    contact_phone = phone or "بيانات الاتصال قيد الإعداد"
    contact_whatsapp = whatsapp or "بيانات الاتصال قيد الإعداد"
    contact_address = _safe_text(settings.get("address"), "بيانات العنوان قيد الإعداد", 250)

    if clean_wa:
        contact_actions = f'''<a href="https://wa.me/{clean_wa}?text={html.escape('مرحباً ' + brand_name + '، أريد التحدث مع خدمة العملاء.')}" target="_blank" rel="noopener" class="px-8 py-3.5 rounded-xl bg-emerald-500 hover:bg-emerald-600 text-white font-black text-center text-sm shadow-lg transition" data-i18n="contact_wa_btn">
            📲 تحدث واتساب الآن
          </a>'''
        promo_contact_cta = f'''<a href="https://wa.me/{clean_wa}?text={html.escape('مرحباً، أريد الاستفسار عن عروض ' + brand_name)}" target="_blank" rel="noopener" class="text-amber-400 hover:underline font-bold mr-2" data-i18n="promo_wa_link">طلب واتساب مباشر</a>'''
        hero_contact_cta = f'''<a href="https://wa.me/{clean_wa}?text={html.escape('مرحباً، أود التواصل مع إدارة ' + brand_name)}" target="_blank" rel="noopener" class="px-8 py-3.5 rounded-xl bg-white/15 backdrop-blur text-white border border-white/30 font-bold text-sm hover:bg-white/25 transition" data-i18n="hero_wa_cta">💬 محادثة واتساب سريعة</a>'''
    else:
        contact_actions = '''<span class="px-8 py-3.5 rounded-xl bg-white/10 border border-white/20 text-slate-300 font-bold text-center text-sm" data-i18n="contact_pending">بيانات التواصل قيد الإعداد</span>'''
        promo_contact_cta = '''<a href="#contact" class="text-amber-400 hover:underline font-bold mr-2" data-i18n="contact_pending">بيانات التواصل قيد الإعداد</a>'''
        hero_contact_cta = '''<a href="#contact" class="px-8 py-3.5 rounded-xl bg-white/15 backdrop-blur text-white border border-white/30 font-bold text-sm hover:bg-white/25 transition" data-i18n="contact_pending">💬 بيانات التواصل قيد الإعداد</a>'''

    # Normalize items with bilingual fields
    raw_source = items if items else DEFAULT_CATALOGS.get(niche, DEFAULT_CATALOGS["general"])
    items = _normalize_store_items(raw_source, niche)

    items_json = _json_for_script(items)

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
      darkMode: 'class',
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
    html[dir="ltr"] .cart-drawer.closed {{ transform: translateX(100%); }}
    .backdrop {{ transition: opacity 0.3s ease; }}
    .backdrop.hidden {{ opacity: 0; pointer-events: none; }}

    /* Universal Seamless Dark Mode System */
    html.dark {{
      color-scheme: dark;
    }}
    html.dark body {{
      background-color: #0b0f17 !important;
      color: #f1f5f9 !important;
    }}
    html.dark header {{
      background-color: rgba(15, 23, 42, 0.95) !important;
      border-color: #1e293b !important;
    }}
    html.dark .bg-white {{
      background-color: #131b2a !important;
      border-color: #1e293b !important;
    }}
    html.dark .bg-slate-50 {{
      background-color: #0f172a !important;
      border-color: #1e293b !important;
    }}
    html.dark .bg-slate-100 {{
      background-color: #1e293b !important;
    }}
    html.dark .text-slate-900,
    html.dark .text-slate-800 {{
      color: #f8fafc !important;
    }}
    html.dark .text-slate-700,
    html.dark .text-slate-600 {{
      color: #cbd5e1 !important;
    }}
    html.dark .text-slate-500 {{
      color: #94a3b8 !important;
    }}
    html.dark .border-slate-200,
    html.dark .border-slate-100,
    html.dark [class*="border-slate-200"] {{
      border-color: #1e293b !important;
    }}
    html.dark #cart-drawer,
    html.dark #checkout-modal > div,
    html.dark #success-modal > div,
    html.dark #order-receipt {{
      background-color: #0f172a !important;
      color: #f8fafc !important;
      border-color: #334155 !important;
    }}
    html.dark input,
    html.dark textarea,
    html.dark select {{
      background-color: #1e293b !important;
      color: #f8fafc !important;
      border-color: #334155 !important;
    }}
    html.dark .cat-btn.bg-white {{
      background-color: #1e293b !important;
      color: #cbd5e1 !important;
      border-color: #334155 !important;
    }}
    html.dark .cat-btn.bg-slate-900 {{
      background-color: {primary} !important;
      color: #0f172a !important;
    }}
  </style>
</head>
<body class="text-slate-800 antialiased min-h-screen flex flex-col selection:bg-brand-500 selection:text-white">
  <a href="#main-content" class="sr-only focus:not-sr-only focus:fixed focus:top-3 focus:left-3 focus:z-[100] focus:rounded-lg focus:bg-white focus:px-4 focus:py-3 focus:text-slate-950">تخطي إلى المحتوى الرئيسي / Skip to main content</a>

  <!-- Top Announcement Bar -->
  <div class="bg-slate-900 text-slate-200 text-xs py-2 px-4 text-center flex items-center justify-between border-b border-slate-800">
    <div class="flex items-center gap-2 mx-auto">
      <span class="inline-block w-2 h-2 rounded-full bg-emerald-400 animate-ping"></span>
      <span id="promo-bar-text" data-i18n="promo_bar">🎉 <b>تسوق عبر المتجر:</b> أضف المنتجات إلى طلبك وأرسله للمراجعة</span>
      {promo_contact_cta}
    </div>
    <div class="flex items-center gap-2">
      <button onclick="toggleStoreTheme()" class="px-2.5 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-amber-400 text-xs font-bold transition flex items-center gap-1.5 border border-slate-700 shadow-sm" id="store-theme-btn" title="تبديل الوضع / Toggle Theme">
        <span id="store-theme-icon">🌙</span> <span id="store-theme-lbl" data-i18n="theme_dark">ليلي</span>
      </button>
      <button onclick="toggleStoreLang()" class="px-2.5 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-cyan-400 text-xs font-bold transition border border-slate-700 shadow-sm" id="store-lang-btn" title="Language / تغيير اللغة" data-i18n="lang_btn">
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
            <h1 class="text-xl sm:text-2xl font-black text-slate-900 leading-tight" data-i18n="brand_name">{html.escape(brand_name)}</h1>
            <p class="text-xs text-slate-500 font-readex" data-i18n="brand_sub">الجودة والأمانة في كل طلب</p>
          </div>
        </a>
      </div>

      <nav class="hidden md:flex items-center gap-8 text-sm font-bold text-slate-600">
        <a href="#hero" class="hover:text-brand-500 transition" data-i18n="nav_home">الرئيسية</a>
        <a href="#catalog" class="hover:text-brand-500 transition" data-i18n="nav_catalog">قائمة المنتجات</a>
        <a href="#features" class="hover:text-brand-500 transition" data-i18n="nav_features">لماذا نحن؟</a>
        <a href="#reviews" class="hover:text-brand-500 transition" data-i18n="nav_reviews">آراء العملاء</a>
        <a href="#contact" class="hover:text-brand-500 transition" data-i18n="nav_contact">تواصل معنا</a>
      </nav>

      <div class="flex items-center gap-3">
        <!-- Floating Cart Trigger -->
        <button onclick="toggleCart(true)" class="relative flex items-center gap-2.5 px-4 py-2.5 rounded-xl font-bold text-white shadow-md hover:shadow-lg transition active:scale-95" style="background:{primary}">
          <span class="text-lg">🛒</span>
          <span class="hidden sm:inline text-sm" data-i18n="cart_btn">السلة</span>
          <span id="cart-counter" class="bg-amber-400 text-slate-950 text-xs px-2 py-0.5 rounded-full font-black">0</span>
        </button>
      </div>
    </div>
  </header>

  <main id="main-content" tabindex="-1">
  <!-- Hero Section -->
  <section id="hero" class="hero-grad text-white py-16 sm:py-24 relative overflow-hidden">
    <div class="absolute inset-0 opacity-10 bg-[radial-gradient(#fff_1px,transparent_1px)] [background-size:16px_16px]"></div>
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10 text-center">
      <div class="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-bold bg-white/10 backdrop-blur border border-white/20 mb-6">
        <span data-i18n="hero_badge">✨ المتجر الرقمي المتكامل • دفع مصري مباشر</span>
      </div>
      <h2 class="text-3xl sm:text-5xl lg:text-6xl font-black leading-tight max-w-4xl mx-auto mb-6" data-i18n="hero_slogan">
        {html.escape(slogan)}
      </h2>
      <p class="text-base sm:text-lg text-white/90 max-w-2xl mx-auto font-readex leading-relaxed mb-10" data-i18n="hero_sub">
        أرسل طلبك من المتجر، وسيتم التواصل معك من التاجر لتأكيد التوافر وطريقة الدفع والتسليم.
      </p>
      <div class="flex flex-wrap items-center justify-center gap-4">
        <a href="#catalog" class="px-8 py-3.5 rounded-xl bg-white text-slate-950 font-black text-sm shadow-xl hover:bg-slate-100 transition hover:scale-105 active:scale-95" data-i18n="hero_cta">
          🛒 تصفح القائمة والأسعار
        </a>
        {hero_contact_cta}
      </div>
    </div>
  </section>

  <!-- Features Grid -->
  <section id="features" class="py-12 bg-white border-b border-slate-200">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
      <div class="p-6 rounded-2xl bg-slate-50 border border-slate-100 flex items-start gap-4">
        <div class="text-3xl">🌿</div>
        <div>
          <h4 class="font-bold text-slate-900 mb-1" data-i18n="feat1_title">طبيعي ومضمون 100%</h4>
          <p class="text-xs text-slate-500 font-readex" data-i18n="feat1_desc">نحرص على أعلى معايير الجودة والفحص قبل التسليم.</p>
        </div>
      </div>
      <div class="p-6 rounded-2xl bg-slate-50 border border-slate-100 flex items-start gap-4">
        <div class="text-3xl">⚡</div>
        <div>
          <h4 class="font-bold text-slate-900 mb-1" data-i18n="feat2_title">توصيل سريع للباب</h4>
          <p class="text-xs text-slate-500 font-readex" data-i18n="feat2_desc">شحن مباشر حتى باب منزلك في وقت قياسي.</p>
        </div>
      </div>
      <div class="p-6 rounded-2xl bg-slate-50 border border-slate-100 flex items-start gap-4">
        <div class="text-3xl">💳</div>
        <div>
          <h4 class="font-bold text-slate-900 mb-1" data-i18n="feat3_title">طرق دفع مرنة</h4>
          <p class="text-xs text-slate-500 font-readex" data-i18n="feat3_desc">فودافون كاش، إنستاباي، فوري، وكاش عند الاستلام.</p>
        </div>
      </div>
      <div class="p-6 rounded-2xl bg-slate-50 border border-slate-100 flex items-start gap-4">
        <div class="text-3xl">🛡️</div>
        <div>
          <h4 class="font-bold text-slate-900 mb-1" data-i18n="feat4_title">خدمة عملاء مباشرة</h4>
          <p class="text-xs text-slate-500 font-readex" data-i18n="feat4_desc">متابعة فورية عبر الواتساب لتلبية كافة الاستفسارات.</p>
        </div>
      </div>
    </div>
  </section>

  <!-- Catalog Section -->
  <section id="catalog" class="py-16 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex-1 w-full">
    <div class="flex flex-col md:flex-row md:items-end justify-between mb-10 gap-4">
      <div>
        <span class="text-xs font-bold text-brand-600 tracking-wider uppercase font-readex" data-i18n="cat_title_badge">قائمة الأصناف المتاحة</span>
        <h3 class="text-2xl sm:text-3xl font-black text-slate-900 mt-1" data-i18n="cat_title">اختر ما يناسبك واطلبه الآن</h3>
      </div>

      <!-- Category Filter Tabs (Rendered by JS) -->
      <div class="flex flex-wrap gap-2" id="category-filters">
        <!-- Rendered by JS -->
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
        <span class="text-xs font-bold text-amber-600 tracking-wider uppercase font-readex" data-i18n="reviews_badge">تقييمات موثقة</span>
        <h3 class="text-2xl sm:text-3xl font-black text-slate-900 mt-1" data-i18n="reviews_title">آراء وتجارب العملاء ⭐⭐⭐⭐⭐</h3>
      </div>
      <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div class="p-6 rounded-2xl bg-white border border-slate-200 shadow-sm">
          <div class="flex items-center justify-between mb-2">
            <b class="text-xs text-slate-900" data-i18n="rev1_name">محمد السعيد</b>
            <span class="text-amber-400 text-xs">★★★★★</span>
          </div>
          <p class="text-xs text-slate-600 font-readex leading-relaxed" data-i18n="rev1_text">
            المنتجات وصلت مطابقة للصور تماماً، وسرعة الاستجابة على الواتساب والتوصيل محترمة جداً.
          </p>
        </div>
        <div class="p-6 rounded-2xl bg-white border border-slate-200 shadow-sm">
          <div class="flex items-center justify-between mb-2">
            <b class="text-xs text-slate-900" data-i18n="rev2_name">سارة إبراهيم</b>
            <span class="text-amber-400 text-xs">★★★★★</span>
          </div>
          <p class="text-xs text-slate-600 font-readex leading-relaxed" data-i18n="rev2_text">
            التغليف فاخر وأصلي والدفع بإنستاباي كان في ثواني، شكراً على الأمانة والاحترافية.
          </p>
        </div>
        <div class="p-6 rounded-2xl bg-white border border-slate-200 shadow-sm">
          <div class="flex items-center justify-between mb-2">
            <b class="text-xs text-slate-900" data-i18n="rev3_name">أحمد حسام</b>
            <span class="text-amber-400 text-xs">★★★★★</span>
          </div>
          <p class="text-xs text-slate-600 font-readex leading-relaxed" data-i18n="rev3_text">
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
          <span class="px-3 py-1 rounded-full bg-emerald-500/20 text-emerald-400 text-xs font-bold border border-emerald-500/30" data-i18n="contact_badge">خدمة العملاء متصلة</span>
          <h3 class="text-2xl sm:text-3xl font-black mt-3 mb-2" data-i18n="contact_title">هل لديك استفسار أو طلب خاص؟</h3>
          <p class="text-slate-300 text-sm font-readex max-w-xl" data-i18n="contact_desc">
            فريق خدمة عملاء المتجر جاهز للرد على استفساراتكم ومتابعة طلباتكم على مدار الساعة.
          </p>
          <div class="flex flex-wrap gap-6 mt-6 text-sm">
            <div class="flex items-center gap-2">
              <span class="text-amber-400">📞</span> <b data-i18n="contact_phone_lbl">هاتف:</b> <span>{html.escape(contact_phone)}</span>
            </div>
            <div class="flex items-center gap-2">
              <span class="text-emerald-400">💬</span> <b data-i18n="contact_wa_lbl">واتساب:</b> <span>{html.escape(contact_whatsapp)}</span>
            </div>
            <div class="flex items-center gap-2">
              <span class="text-sky-400">📍</span> <b data-i18n="contact_addr_lbl">العنوان:</b> <span>{html.escape(contact_address)}</span>
            </div>
          </div>
        </div>
        <div class="flex flex-col sm:flex-row gap-4 w-full lg:w-auto">
          {contact_actions}
          {f'''<a href="tel:{phone}" class="px-8 py-3.5 rounded-xl bg-white/10 hover:bg-white/20 border border-white/20 text-white font-bold text-center text-sm transition" data-i18n="contact_call_btn">📞 اتصل هاتفياً</a>''' if phone else ''}
        </div>
      </div>
    </div>
  </section>

  <!-- Footer -->
  </main>
  <footer class="bg-slate-950 text-slate-400 py-8 border-t border-slate-800 text-xs">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between gap-4">
      <div>
        <p>© 2026 <b data-i18n="brand_name">{html.escape(brand_name)}</b> — <span data-i18n="footer_rights">جميع الحقوق محفوظة.</span></p>
      </div>
      <div class="flex items-center gap-3 text-slate-500">
        <span data-i18n="footer_powered">مدعوم بواسطة وكالة</span>
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
        <h3 class="font-black text-lg text-slate-900" data-i18n="cart_title">سلة مشترياتك</h3>
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
        <input type="text" id="cart-promo-input" data-i18n="cart_promo_ph" placeholder="كود الخصم (WELCOME10)" class="flex-1 px-3 py-1.5 rounded-xl border border-slate-300 text-xs uppercase focus:outline-none focus:ring-1 focus:ring-brand-500">
        <button onclick="applyCartPromo()" data-i18n="cart_promo_apply" class="px-3 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-white text-xs font-bold">تطبيق</button>
      </div>

      <div class="space-y-2 mb-4 text-sm font-readex">
        <div class="flex justify-between text-slate-500">
          <span data-i18n="cart_subtotal_lbl">المجموع الفرعي:</span>
          <span id="cart-subtotal" class="font-bold text-slate-800">0 ج.م</span>
        </div>
        <div class="flex justify-between text-emerald-600" id="cart-discount-row" style="display:none">
          <span data-i18n="cart_discount_lbl">الخصم المطبق:</span>
          <span id="cart-discount" class="font-bold">0 ج.م</span>
        </div>
        <div class="flex justify-between text-slate-500">
          <span data-i18n="cart_shipping_lbl">رسوم التوصيل:</span>
          <span id="cart-shipping" class="font-bold text-emerald-600">20 ج.م</span>
        </div>
        <div class="flex justify-between text-base font-black text-slate-900 pt-2 border-t border-slate-200">
          <span data-i18n="cart_total_lbl">الإجمالي النهائي:</span>
          <span id="cart-total" class="text-brand-600">0 ج.م</span>
        </div>
      </div>
      <button id="checkout-btn" onclick="openCheckoutModal()" disabled class="w-full py-3.5 rounded-xl font-black text-white text-sm shadow-md transition disabled:opacity-50 disabled:cursor-not-allowed" style="background:{primary}" data-i18n="cart_checkout_btn">
        📦 متابعة طلب التاجر
      </button>
    </div>
  </aside>

  <!-- Checkout Modal -->
  <div id="checkout-modal" class="backdrop hidden fixed inset-0 bg-slate-950/70 z-50 flex items-center justify-center p-4">
    <div class="bg-white rounded-3xl max-w-lg w-full p-6 sm:p-8 shadow-2xl relative text-right">
      <div class="flex items-center justify-between pb-4 mb-4 border-b border-slate-100">
        <div>
          <h3 class="text-lg font-black text-slate-900" data-i18n="checkout_modal_title">إرسال طلب إلى التاجر 🇪🇬</h3>
          <p class="text-xs text-slate-500 font-readex" data-i18n="checkout_modal_sub">سيتواصل التاجر لتأكيد الطلب وطريقة الدفع؛ لا تُعالج أي دفعة هنا.</p>
        </div>
        <button onclick="closeCheckoutModal()" class="w-8 h-8 rounded-full bg-slate-100 text-slate-500 hover:bg-slate-200 flex items-center justify-center font-bold">✕</button>
      </div>

      <form onsubmit="submitOrder(event)" class="space-y-4">
        <div>
          <label class="block text-xs font-bold text-slate-700 mb-1" data-i18n="checkout_name_lbl">الاسم بالكامل *</label>
          <input type="text" id="cust-name" required data-i18n="checkout_name_ph" placeholder="مثال: أحمد محمود" class="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500">
        </div>
        <div>
          <label class="block text-xs font-bold text-slate-700 mb-1" data-i18n="checkout_phone_lbl">رقم الهاتف / الواتساب *</label>
          <input type="tel" id="cust-phone" required data-i18n="checkout_phone_ph" placeholder="مثال: 01012345678" class="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500">
        </div>
        <div>
          <label class="block text-xs font-bold text-slate-700 mb-1" data-i18n="checkout_address_lbl">عنوان التوصيل بالتفصيل *</label>
          <textarea id="cust-address" required rows="2" data-i18n="checkout_address_ph" placeholder="المدينة، الحي، اسم الشارع، رقم العمارة والشقة" class="w-full px-3.5 py-2 rounded-xl border border-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"></textarea>
        </div>

        <div>
          <label class="block text-xs font-bold text-slate-700 mb-1" data-i18n="checkout_payment_lbl">طريقة الدفع</label>
          <div class="rounded-xl border border-slate-200 p-3 bg-slate-50 text-xs text-slate-600 font-readex space-y-2">
            <label class="flex items-center gap-2 cursor-pointer">
              <input type="radio" name="pay_method" value="cash_on_delivery" checked class="text-brand-500">
              <span class="font-bold text-slate-800" data-i18n="checkout_payment_opt">الدفع عند الاستلام (Cash on Delivery)</span>
            </label>
            <p class="text-[11px] text-slate-500 pr-5" data-i18n="checkout_payment_desc">سيحدد التاجر طريقة الدفع والتسليم بعد مراجعة الطلب.</p>
          </div>
        </div>

        <button type="submit" id="submit-order-btn" class="w-full py-3.5 rounded-xl font-black text-white text-sm shadow-lg transition" style="background:{primary}" data-i18n="checkout_submit_btn">
          ✅ تأكيد وإرسال الطلب الآن
        </button>
      </form>
    </div>
  </div>

  <!-- Success Modal -->
  <div id="success-modal" class="backdrop hidden fixed inset-0 bg-slate-950/70 z-50 flex items-center justify-center p-4">
    <div class="bg-white rounded-3xl max-w-md w-full p-8 text-center shadow-2xl relative">
      <div class="w-16 h-16 rounded-full bg-emerald-100 text-emerald-600 flex items-center justify-center text-3xl mx-auto mb-4">
        ✓
      </div>
      <h3 class="text-xl font-black text-slate-900 mb-1" data-i18n="success_modal_title">تم تأكيد طلبك بنجاح! 🎉</h3>
      <p class="text-xs text-slate-500 mb-6 font-readex" data-i18n="success_modal_sub">
        تم استلام بيانات طلبك بنجاح وجاري تجهيزه للتوصيل.
      </p>

      <div class="bg-slate-50 rounded-2xl p-4 text-xs font-readex space-y-2 mb-6 border border-slate-100 text-right" id="order-receipt">
        <div class="flex justify-between"><span class="text-slate-400" data-i18n="success_order_id_lbl">رقم الأوردر:</span> <b id="res-order-id" class="text-slate-800">#2026</b></div>
        <div class="flex justify-between"><span class="text-slate-400" data-i18n="success_total_lbl">إجمالي المبلغ:</span> <b id="res-total" class="text-brand-600">0 ج.م</b></div>
        <div class="flex justify-between"><span class="text-slate-400" data-i18n="success_method_lbl">طريقة الدفع:</span> <b id="res-payment-method" class="text-slate-800" data-i18n="checkout_payment_opt">بانتظار تأكيد التاجر</b></div>
        <div class="flex justify-between"><span class="text-slate-400" data-i18n="success_ref_lbl">المرجع / الكود:</span> <b id="res-payment-ref" class="text-slate-800 font-mono">ORDER-2026</b></div>
      </div>

      <div class="space-y-3">
        <a id="res-whatsapp-link" href="#" target="_blank" rel="noopener" class="w-full block py-3.5 rounded-xl font-black text-white text-xs bg-emerald-500 hover:bg-emerald-600 shadow-md transition" data-i18n="success_wa_btn">
          💬 إرسال تفاصيل الأوردر للواتساب للتأكيد
        </a>
        <button onclick="closeSuccessModal()" class="w-full py-2.5 rounded-xl font-bold text-slate-500 hover:bg-slate-100 text-xs transition" data-i18n="success_close_btn">
          إغلاق ومتابعة التسوق
        </button>
      </div>
    </div>
  </div>

  <script>
    const SITE_JOB_ID = {job_id};
    const STORE_NAME = {_json_for_script(brand_name)};
    const WA_PHONE = '{clean_wa}';
    const PRODUCTS = {items_json};

    let cart = {{}};
    let activeFilter = 'الكل';
    let appliedPromoDiscount = 0;
    let storeLang = 'ar';
    let isStoreDark = false;

    function escapeProductHtml(value) {{
      return String(value ?? '').replace(/[&<>"']/g, char => ({{ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }}[char]));
    }}

    const I18N = {{
      ar: {{
        promo_bar: '🎉 <b>عروض حصرية:</b> كود خصم 10%: <b>WELCOME10</b> | 🚚 توصيل سريع لجميع المحافظات',
        promo_bar_text: '🎉 <b>عروض حصرية:</b> كود خصم 10%: <b>WELCOME10</b> | 🚚 توصيل سريع لجميع المحافظات',
        promo_wa_link: 'طلب واتساب مباشر',
        theme_dark: 'ليلي',
        theme_light: 'نهاري',
        lang_btn: 'English',
        brand_name: {_json_for_script(brand_name)},
        brand_sub: 'المتجر الإلكتروني المعتمد 🇪🇬',
        nav_home: 'الرئيسية',
        nav_catalog: 'قائمة المنتجات',
        nav_features: 'لماذا نحن؟',
        nav_reviews: 'آراء العملاء',
        nav_contact: 'تواصل معنا',
        cart_btn: 'السلة',
        hero_badge: '✨ المتجر الرقمي المتكامل • دفع مصري مباشر',
        hero_slogan: {_json_for_script(slogan)},
        hero_sub: 'أرسل طلبك من المتجر، وسيتم التواصل معك من التاجر لتأكيد التوافر وطريقة الدفع والتسليم.',
        hero_cta: '🛒 تصفح القائمة والأسعار',
        hero_wa_cta: '💬 محادثة واتساب سريعة',
        contact_pending: 'بيانات التواصل قيد الإعداد',
        feat1_title: 'طبيعي ومضمون 100%',
        feat1_desc: 'نحرص على أعلى معايير الجودة والفحص قبل التسليم.',
        feat2_title: 'توصيل سريع للباب',
        feat2_desc: 'شحن مباشر حتى باب منزلك في وقت قياسي.',
        feat3_title: 'طرق دفع مرنة',
        feat3_desc: 'فودافون كاش، إنستاباي، فوري، وكاش عند الاستلام.',
        feat4_title: 'خدمة عملاء مباشرة',
        feat4_desc: 'متابعة فورية عبر الواتساب لتلبية كافة الاستفسارات.',
        cat_title_badge: 'قائمة الأصناف المتاحة',
        cat_title: 'اختر ما يناسبك واطلبه الآن',
        cat_all: 'الكل',
        empty_cat: 'لا توجد منتجات في هذا القسم حالياً',
        add_to_cart: '+ أضف للسلة',
        price_lbl: 'السعر:',
        currency: 'ج.م',
        reviews_badge: 'تقييمات موثقة',
        reviews_title: 'آراء وتجارب العملاء ⭐⭐⭐⭐⭐',
        rev1_name: 'محمد السعيد',
        rev1_text: 'المنتجات وصلت مطابقة للصور تماماً، وسرعة الاستجابة على الواتساب والتوصيل محترمة جداً.',
        rev2_name: 'سارة إبراهيم',
        rev2_text: 'التغليف فاخر وأصلي والدفع بإنستاباي كان في ثواني، شكراً على الأمانة والاحترافية.',
        rev3_name: 'أحمد حسام',
        rev3_text: 'أفضل تجربة شراء أونلاين في مصر، بالتأكيد هكرر الطلب تاني.',
        contact_badge: 'خدمة العملاء متصلة',
        contact_title: 'هل لديك استفسار أو طلب خاص؟',
        contact_desc: 'فريق خدمة عملاء المتجر جاهز للرد على استفساراتكم ومتابعة طلباتكم على مدار الساعة.',
        contact_phone_lbl: 'هاتف:',
        contact_wa_lbl: 'واتساب:',
        contact_addr_lbl: 'العنوان:',
        contact_wa_btn: '📲 تحدث واتساب الآن',
        contact_call_btn: '📞 اتصل هاتفياً',
        footer_rights: 'جميع الحقوق محفوظة.',
        footer_powered: 'مدعوم بواسطة وكالة',
        cart_title: 'سلة مشترياتك',
        cart_items_count: 'عناصر',
        cart_empty_title: 'سلتك فارغة حالياً',
        cart_empty_sub: 'تصفح القائمة وأضف منتجاتك المفضلة',
        cart_promo_ph: 'كود الخصم (WELCOME10)',
        cart_promo_apply: 'تطبيق',
        cart_subtotal_lbl: 'المجموع الفرعي:',
        cart_discount_lbl: 'الخصم المطبق:',
        cart_shipping_lbl: 'رسوم التوصيل:',
        cart_total_lbl: 'الإجمالي النهائي:',
        cart_checkout_btn: '📦 متابعة طلب التاجر',
        checkout_modal_title: 'إرسال طلب إلى التاجر 🇪🇬',
        checkout_modal_sub: 'سيتواصل التاجر لتأكيد الطلب وطريقة الدفع؛ لا تُعالج أي دفعة هنا.',
        checkout_name_lbl: 'الاسم بالكامل *',
        checkout_name_ph: 'مثال: أحمد محمود',
        checkout_phone_lbl: 'رقم الهاتف / الواتساب *',
        checkout_phone_ph: 'مثال: 01012345678',
        checkout_address_lbl: 'عنوان التوصيل بالتفصيل *',
        checkout_address_ph: 'المدينة، الحي، اسم الشارع، رقم العمارة والشقة',
        checkout_payment_lbl: 'حالة الدفع',
        checkout_payment_opt: 'بانتظار تأكيد التاجر',
        checkout_payment_desc: 'سيحدد التاجر طريقة الدفع والتسليم بعد مراجعة الطلب.',
        checkout_submit_btn: '✅ تأكيد وإرسال الطلب الآن',
        success_modal_title: 'تم تأكيد طلبك بنجاح! 🎉',
        success_modal_sub: 'تم استلام بيانات طلبك بنجاح وجاري تجهيزه للتوصيل.',
        success_order_id_lbl: 'رقم الأوردر:',
        success_total_lbl: 'إجمالي المبلغ:',
        success_method_lbl: 'طريقة الدفع:',
        success_ref_lbl: 'المرجع / الكود:',
        success_wa_btn: '💬 إرسال تفاصيل الأوردر للواتساب للتأكيد',
        success_close_btn: 'إغلاق ومتابعة التسوق'
      }},
      en: {{
        promo_bar: '🎉 <b>Exclusive Deals:</b> 10% Off Code: <b>WELCOME10</b> | 🚚 Fast Delivery Nationwide',
        promo_bar_text: '🎉 <b>Exclusive Deals:</b> 10% Off Code: <b>WELCOME10</b> | 🚚 Fast Delivery Nationwide',
        promo_wa_link: 'Direct WhatsApp Order',
        theme_dark: 'Dark',
        theme_light: 'Light',
        lang_btn: 'العربية',
        brand_name: {_json_for_script(brand_name)},
        brand_sub: 'Certified Online Store 🇪🇬',
        nav_home: 'Home',
        nav_catalog: 'Catalog',
        nav_features: 'Features',
        nav_reviews: 'Reviews',
        nav_contact: 'Contact',
        cart_btn: 'Cart',
        hero_badge: '✨ Full-Featured Digital Store • Express Delivery',
        hero_slogan: {_json_for_script(slogan_en)},
        hero_sub: 'Submit your order directly; our merchant team will contact you immediately to confirm delivery and payment.',
        hero_cta: '🛒 Browse Catalog & Prices',
        hero_wa_cta: '💬 Direct WhatsApp Chat',
        contact_pending: 'Contact Info In Progress',
        feat1_title: '100% Authentic Quality',
        feat1_desc: 'Strict quality control and lab inspection before dispatch.',
        feat2_title: 'Direct Fast Delivery',
        feat2_desc: 'Express door-to-door delivery across all Egyptian governorates.',
        feat3_title: 'Flexible Payment',
        feat3_desc: 'Vodafone Cash, InstaPay, Fawry, and Cash on Delivery.',
        feat4_title: 'Instant Support',
        feat4_desc: 'Direct WhatsApp and phone assistance around the clock.',
        cat_title_badge: 'Available Collections',
        cat_title: 'Select Your Favorites and Order Now',
        cat_all: 'All',
        empty_cat: 'No items found in this section right now',
        add_to_cart: '+ Add to Cart',
        price_lbl: 'Price:',
        currency: 'EGP',
        reviews_badge: 'Verified Reviews',
        reviews_title: 'Customer Feedback ⭐⭐⭐⭐⭐',
        rev1_name: 'Mohamed El-Saeed',
        rev1_text: 'Products arrived exactly as pictured, fast WhatsApp response and great delivery.',
        rev2_name: 'Sara Ibrahim',
        rev2_text: 'Luxury packaging, InstaPay payment took seconds, thank you for the professionalism.',
        rev3_name: 'Ahmed Hossam',
        rev3_text: 'Best online shopping experience in Egypt, will definitely order again.',
        contact_badge: 'Customer Support Online',
        contact_title: 'Have a Question or Special Request?',
        contact_desc: 'Merchant customer service team is ready to answer inquiries and track orders around the clock.',
        contact_phone_lbl: 'Phone:',
        contact_wa_lbl: 'WhatsApp:',
        contact_addr_lbl: 'Address:',
        contact_wa_btn: '📲 Chat on WhatsApp Now',
        contact_call_btn: '📞 Call Now',
        footer_rights: 'All rights reserved.',
        footer_powered: 'Powered by Agency',
        cart_title: 'Your Shopping Cart',
        cart_items_count: 'items',
        cart_empty_title: 'Your cart is currently empty',
        cart_empty_sub: 'Explore catalog items and add to cart',
        cart_promo_ph: 'Promo code (WELCOME10)',
        cart_promo_apply: 'Apply',
        cart_subtotal_lbl: 'Subtotal:',
        cart_discount_lbl: 'Discount Applied:',
        cart_shipping_lbl: 'Delivery Fee:',
        cart_total_lbl: 'Total Amount:',
        cart_checkout_btn: '📦 Proceed with Merchant Order',
        checkout_modal_title: 'Submit Order Request 🇪🇬',
        checkout_modal_sub: 'The merchant will contact you to confirm; no payment charged here.',
        checkout_name_lbl: 'Full Name *',
        checkout_name_ph: 'e.g. Ahmed Mahmoud',
        checkout_phone_lbl: 'Phone / WhatsApp *',
        checkout_phone_ph: 'e.g. 01012345678',
        checkout_address_lbl: 'Delivery Address *',
        checkout_address_ph: 'City, district, street, building and apartment',
        checkout_payment_lbl: 'Payment Status',
        checkout_payment_opt: 'Awaiting Merchant Confirmation',
        checkout_payment_desc: 'Merchant confirms payment method and delivery after reviewing.',
        checkout_submit_btn: '✅ Confirm & Send Order Now',
        success_modal_title: 'Order Confirmed Successfully! 🎉',
        success_modal_sub: 'Your order request was received and is being prepared for delivery.',
        success_order_id_lbl: 'Order ID:',
        success_total_lbl: 'Total Amount:',
        success_method_lbl: 'Payment Method:',
        success_ref_lbl: 'Reference / Code:',
        success_wa_btn: '💬 Send Order Details via WhatsApp',
        success_close_btn: 'Close & Continue Shopping'
      }}
    }};

    function renderCategoryFilters() {{
      const container = document.getElementById('category-filters');
      if (!container) return;
      const isEn = (storeLang === 'en');
      const allLabel = isEn ? 'All' : 'الكل';

      const catMap = new Map();
      catMap.set('الكل', {{ ar: 'الكل', en: 'All' }});
      PRODUCTS.forEach(p => {{
        const arCat = p.category || 'عام';
        const enCat = p.category_en || arCat;
        if (!catMap.has(arCat)) {{
          catMap.set(arCat, {{ ar: arCat, en: enCat }});
        }}
      }});

      let html = '';
      catMap.forEach((val, key) => {{
        const label = isEn ? val.en : val.ar;
        const isSelected = (activeFilter === key);
        const cls = isSelected 
          ? 'cat-btn px-4 py-2 rounded-xl text-xs font-bold transition bg-slate-900 text-white'
          : 'cat-btn px-4 py-2 rounded-xl text-xs font-bold transition bg-white text-slate-600 border border-slate-200 hover:bg-slate-100';
        html += `<button onclick="filterCategory('${{escapeProductHtml(key)}}')" class="${{cls}}" data-cat="${{escapeProductHtml(key)}}">${{escapeProductHtml(label)}}</button>`;
      }});
      container.innerHTML = html;
    }}

    function renderProducts() {{
      const grid = document.getElementById('products-grid');
      if (!grid) return;
      const isEn = (storeLang === 'en');
      const dict = I18N[storeLang] || I18N.ar;
      const filtered = (activeFilter === 'الكل') 
        ? PRODUCTS 
        : PRODUCTS.filter(p => p.category === activeFilter);
        
      if (!filtered.length) {{
        grid.innerHTML = `<div class="col-span-full py-12 text-center text-slate-400 font-bold">${{dict.empty_cat}}</div>`;
        return;
      }}

      grid.innerHTML = filtered.map(p => {{
        const id = Number(p.id);
        if (!Number.isSafeInteger(id) || id < 1) return '';
        const price = Number(p.price);
        const safePrice = Number.isFinite(price) && price >= 0 ? price : 0;
        const category = escapeProductHtml(isEn && p.category_en ? p.category_en : p.category);
        const badge = escapeProductHtml(isEn && p.badge_en ? p.badge_en : p.badge);
        const title = escapeProductHtml(isEn && p.title_en ? p.title_en : p.title);
        const description = escapeProductHtml(isEn && p.desc_en ? p.desc_en : (p.description || (isEn ? 'Certified high-quality item.' : 'صنف عالي الجودة ومضمون تم اختياره بعناية.')));
        const imageUrl = p.image_url ? escapeProductHtml(p.image_url) : '';
        const addBtnText = dict.add_to_cart;
        const priceLabel = dict.price_lbl;
        const curr = dict.currency;
        return `
        <div class="bg-white rounded-3xl border border-slate-200/80 p-5 shadow-sm hover:shadow-xl transition-all duration-300 flex flex-col justify-between group hover:-translate-y-1">
          <div>
            ${{imageUrl ? `
            <div class="overflow-hidden rounded-2xl mb-4 bg-slate-100 aspect-square flex items-center justify-center">
              <img src="${{imageUrl}}" alt="${{title}}" class="w-full h-full object-cover group-hover:scale-105 transition duration-500" loading="lazy" onerror="this.onerror=null;this.parentElement.innerHTML='<div class=\'w-full h-full flex items-center justify-center text-4xl bg-slate-100\'>🛍️</div>';">
            </div>` : `
            <div class="overflow-hidden rounded-2xl mb-4 bg-gradient-to-br from-slate-100 to-slate-200 aspect-square flex items-center justify-center text-4xl">
              🛍️
            </div>`}}
            <div class="flex items-center justify-between mb-3">
              <span class="text-[11px] font-bold px-2.5 py-1 rounded-full bg-slate-100 text-slate-600 font-readex">
                ${{category}}
              </span>
              ${{badge ? `<span class="text-[11px] font-black px-2.5 py-1 rounded-full text-brand-600" style="background:{pal['badge_bg']};color:{pal['badge_text']}">★ ${{badge}}</span>` : ''}}
            </div>
            
            <h4 class="text-base font-black text-slate-900 mb-2 leading-snug group-hover:text-brand-600 transition">
              ${{title}}
            </h4>
            
            <p class="text-xs text-slate-500 font-readex leading-relaxed mb-6">
              ${{description}}
            </p>
          </div>

          <div class="pt-4 border-t border-slate-100 flex items-center justify-between">
            <div>
              <span class="text-xs text-slate-400 font-bold">${{priceLabel}}</span>
              <div class="text-lg font-black text-slate-900">${{safePrice.toLocaleString()}} <span class="text-xs font-bold text-slate-500">${{curr}}</span></div>
            </div>

            <button onclick="addToCart(${{id}})" class="flex items-center gap-1.5 px-4 py-2.5 rounded-xl font-bold text-white text-xs shadow-md hover:shadow-lg transition active:scale-95" style="background:{primary}">
              <span>${{addBtnText}}</span>
            </button>
          </div>
        </div>
      `;
      }}).join('');
    }}

    function filterCategory(cat) {{
      activeFilter = cat;
      renderCategoryFilters();
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
      const isEn = (storeLang === 'en');
      const dict = I18N[storeLang] || I18N.ar;
      const countEl = document.getElementById('cart-counter');
      const badgeEl = document.getElementById('cart-items-total-badge');
      const itemsContainer = document.getElementById('cart-items');
      const subtotalEl = document.getElementById('cart-subtotal');
      const totalEl = document.getElementById('cart-total');
      const checkoutBtn = document.getElementById('checkout-btn');

      const ids = Object.keys(cart);
      const totalCount = ids.reduce((sum, id) => sum + cart[id], 0);

      if (countEl) countEl.textContent = totalCount;
      if (badgeEl) badgeEl.textContent = totalCount + ' ' + (dict.cart_items_count || 'عناصر');

      if (!ids.length) {{
        itemsContainer.innerHTML = `
          <div class="h-64 flex flex-col items-center justify-center text-center text-slate-400">
            <span class="text-4xl mb-2">🛒</span>
            <p class="text-sm font-bold">${{dict.cart_empty_title || 'سلتك فارغة حالياً'}}</p>
            <p class="text-xs text-slate-400 mt-1">${{dict.cart_empty_sub || 'تصفح القائمة وأضف منتجاتك المفضلة'}}</p>
          </div>
        `;
        if (subtotalEl) subtotalEl.textContent = '0 ' + dict.currency;
        if (totalEl) totalEl.textContent = '0 ' + dict.currency;
        if (checkoutBtn) checkoutBtn.disabled = true;
        return;
      }}

      if (checkoutBtn) checkoutBtn.disabled = false;
      let subtotal = 0;

      itemsContainer.innerHTML = ids.map(id => {{
        const p = PRODUCTS.find(prod => prod.id == id);
        if (!p) return '';
        const itemTitle = escapeProductHtml(isEn && p.title_en ? p.title_en : p.title);
        const rawPrice = Number(p.price);
        const itemPrice = Number.isFinite(rawPrice) && rawPrice >= 0 ? rawPrice : 0;
        const lineTotal = itemPrice * cart[id];
        subtotal += lineTotal;
        return `
          <div class="flex items-center justify-between p-3.5 rounded-2xl bg-slate-50 border border-slate-100">
            <div class="flex-1 min-w-0 pr-2">
              <h5 class="text-xs font-black text-slate-900 truncate">${{itemTitle}}</h5>
              <div class="text-[11px] text-slate-500">${{itemPrice.toLocaleString()}} ${{dict.currency}} × ${{cart[id]}}</div>
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
      if (subtotalEl) subtotalEl.textContent = subtotal.toLocaleString() + ' ' + dict.currency;
      const shippingEl = document.getElementById('cart-shipping');
      if (shippingEl) shippingEl.textContent = shipping.toLocaleString() + ' ' + dict.currency;
      const discRow = document.getElementById('cart-discount-row');
      const discEl = document.getElementById('cart-discount');
      if (discRow && discEl) {{
        if (appliedPromoDiscount > 0) {{
          discRow.style.display = 'flex';
          discEl.textContent = `${{discountVal.toFixed(0)}} ${{dict.currency}} (-${{appliedPromoDiscount}}%)`;
        }} else {{
          discRow.style.display = 'none';
        }}
      }}
      if (totalEl) totalEl.textContent = Math.max(0, (subtotal - discountVal + shipping)).toLocaleString() + ' ' + dict.currency;
    }}

    function applyCartPromo() {{
      const code = (document.getElementById('cart-promo-input').value || '').trim().toUpperCase();
      if (code === 'WELCOME10') appliedPromoDiscount = 10;
      else if (code === 'EGYPT2026') appliedPromoDiscount = 15;
      else if (code === 'AUTOCORP') appliedPromoDiscount = 20;
      else {{
        alert(storeLang === 'en' ? 'Invalid or expired promo code' : 'كود الخصم غير صحيح أو منتهي الصلاحية');
        return;
      }}
      alert(storeLang === 'en' ? `🎉 Promo code applied successfully (-${{appliedPromoDiscount}}%)!` : `🎉 تم تفعيل كود الخصم بنجاح (-${{appliedPromoDiscount}}%)!`);
      updateCartUI();
    }}

    function applyStoreTheme(dark) {{
      isStoreDark = !!dark;
      if (isStoreDark) {{
        document.documentElement.classList.add('dark');
      }} else {{
        document.documentElement.classList.remove('dark');
      }}
      try {{ localStorage.setItem('store_theme', isStoreDark ? 'dark' : 'light'); }} catch (e) {{}}
      const icon = document.getElementById('store-theme-icon');
      const lbl = document.getElementById('store-theme-lbl');
      const dict = I18N[storeLang] || I18N.ar;
      if (icon) icon.textContent = isStoreDark ? '🌙' : '☀️';
      if (lbl) lbl.textContent = isStoreDark ? dict.theme_dark : dict.theme_light;
    }}

    function toggleStoreTheme() {{
      applyStoreTheme(!isStoreDark);
    }}

    function applyStoreLang(lang) {{
      storeLang = (lang === 'en') ? 'en' : 'ar';
      document.documentElement.lang = storeLang;
      document.documentElement.dir = (storeLang === 'ar') ? 'rtl' : 'ltr';
      try {{ localStorage.setItem('store_lang', storeLang); }} catch (e) {{}}

      const dict = I18N[storeLang] || I18N.ar;

      const btn = document.getElementById('store-lang-btn');
      if (btn) btn.textContent = dict.lang_btn;

      const themeLbl = document.getElementById('store-theme-lbl');
      if (themeLbl) themeLbl.textContent = isStoreDark ? dict.theme_dark : dict.theme_light;

      document.querySelectorAll('[data-i18n]').forEach(el => {{
        const key = el.getAttribute('data-i18n');
        if (dict[key]) {{
          if (el.tagName === 'INPUT' || el.tagName === 'TEXTAREA') {{
            el.placeholder = dict[key];
          }} else {{
            el.innerHTML = dict[key];
          }}
        }}
      }});

      renderCategoryFilters();
      renderProducts();
      updateCartUI();
    }}

    function toggleStoreLang() {{
      applyStoreLang(storeLang === 'ar' ? 'en' : 'ar');
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

    async function submitOrder(e) {{
      e.preventDefault();
      const btn = document.getElementById('submit-order-btn');
      btn.disabled = true;
      btn.textContent = (storeLang === 'en') ? '⏳ Processing Order...' : '⏳ جاري معالجة وتأكيد الطلب...';

      const cartItemsPayload = Object.keys(cart).map(id => {{
        const p = PRODUCTS.find(x => x.id == id);
        return {{
          id: id,
          title: (storeLang === 'en' && p?.title_en) ? p.title_en : (p?.title || 'عنصر'),
          price: p?.price || 0,
          quantity: cart[id]
        }};
      }});

      const shipping = 20;
      const subtotal = cartItemsPayload.reduce((s, it) => s + it.price * it.quantity, 0);
      const total = subtotal + shipping;
      const payMethod = document.querySelector('input[name="pay_method"]:checked')?.value || 'cash_on_delivery';

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
          headers: {{ 'Content-Type': 'application/json', 'Idempotency-Key': crypto.randomUUID() }},
          body: JSON.stringify(orderData)
        }});

        const result = await res.json().catch(() => ({{}}));
        if (!res.ok) {{
          throw new Error(result.detail || 'Unable to submit the order request.');
        }}

        closeCheckoutModal();

        document.getElementById('res-order-id').textContent = '#' + (result.id || result.order_id || '2026');
        document.getElementById('res-total').textContent = (result.total_egp ?? total) + (storeLang === 'en' ? ' EGP' : ' ج.م');
        document.getElementById('res-payment-method').textContent = (storeLang === 'en') ? 'Awaiting Merchant Confirmation' : 'بانتظار تأكيد التاجر';
        document.getElementById('res-payment-ref').textContent = result.payment_ref || 'ORDER-REQUESTED';

        const waLines = [
          "مرحباً " + STORE_NAME + " 👋",
          "لقد قمت بعمل طلب جديد عبر المتجر:",
          "• رقم الطلب: #" + (result.id || result.order_id || ""),
          "• الاسم: " + orderData.customer_name,
          "• الهاتف: " + orderData.customer_phone,
          "• العنوان: " + orderData.customer_address,
          "• الإجمالي: " + (result.total_egp ?? total) + " ج.م",
          "• طريقة الدفع: " + payMethod,
          "• المرجع: " + (result.payment_ref || ""),
          "برجاء تأكيد الموعد للتوصيل!"
        ];
        const waMsg = encodeURIComponent(waLines.join(String.fromCharCode(10)));
        const confirmationLink = document.getElementById('res-whatsapp-link');
        if (WA_PHONE) {{
          confirmationLink.href = `https://wa.me/${{WA_PHONE}}?text=${{waMsg}}`;
          confirmationLink.target = '_blank';
        }} else {{
          confirmationLink.href = '#contact';
          confirmationLink.removeAttribute('target');
          confirmationLink.textContent = (storeLang === 'en') ? 'Contact info in progress' : 'بيانات التواصل قيد الإعداد';
        }}

        document.getElementById('success-modal').classList.remove('hidden');
      }} catch (err) {{
        alert((storeLang === 'en') ? ('Error submitting order: ' + err.message) : ('حدث خطأ أثناء إرسال الطلب: ' + err.message));
      }} finally {{
        btn.disabled = false;
        btn.textContent = (storeLang === 'en') ? '✅ Confirm & Send Order Now' : '✅ تأكيد وإرسال الطلب الآن';
      }}
    }}

    window.addEventListener('DOMContentLoaded', () => {{
      let savedTheme = 'light';
      try {{ savedTheme = localStorage.getItem('store_theme') || 'light'; }} catch (e) {{}}
      applyStoreTheme(savedTheme === 'dark');

      let savedLang = 'ar';
      try {{ savedLang = localStorage.getItem('store_lang') || 'ar'; }} catch (e) {{}}
      applyStoreLang(savedLang);
    }});
  </script>
</body>
</html>"""
    return html_code

