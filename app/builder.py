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
    "honey": [
        {"title": "عسل سدر جبلي يمني دوعني نخب أول (كيلو)", "price": 420, "category": "عسل طبيعي فاخر", "badge": "الأكثر طلباً", "desc": "أجود أنواع السدر الجبلي الطبيعي المفحوص معملياً، غني بالمعادن ومضادات الأكسدة.", "image_url": "https://images.unsplash.com/photo-1587049352846-4a222e784d38?auto=format&fit=crop&w=600&q=80"},
        {"title": "عسل حبة البركة الصافي المنقى (نصف كيلو)", "price": 190, "category": "أعسال علاجية", "badge": "مقوي للمناعة", "desc": "عسل نقي مغذى على أزهار حبة البركة، مثالي لتقوية الجهاز المناعي والجهاز التنفسي.", "image_url": "https://images.unsplash.com/photo-1587049352851-8d4e89133924?auto=format&fit=crop&w=600&q=80"},
        {"title": "عسل زهور الموالح الطبيعي (كيلو)", "price": 150, "category": "عسل الزهور", "badge": "خفيف ولذيذ", "desc": "عسل حمضيات خفيف ولذيذ وغني بفيتامين C، محبب جداً للأطفال وطاقة يومية طبيعية.", "image_url": "https://images.unsplash.com/photo-1582793988951-9aed5509eb97?auto=format&fit=crop&w=600&q=80"},
        {"title": "غذاء ملكات النحل الصافي الطازج (50 جم)", "price": 240, "category": "مشتقات النحل", "badge": "طاقة ونشاط", "desc": "غذاء ملكي نقي 100% مستخرج طازجاً، محفز طبيعي للنشاط الذهني والبدني.", "image_url": "https://images.unsplash.com/photo-1558642452-9d2a7deb7f62?auto=format&fit=crop&w=600&q=80"},
        {"title": "بوكس التوفير الملكي (3 برطمانات متنوعة + شمع)", "price": 520, "category": "بكجات التوفير", "badge": "وفر 25%", "desc": "سدر جبلي + حبة بركة + زهور موالح + قطعة شمع طبيعي في علبة إهداء فاخرة.", "image_url": "https://images.unsplash.com/photo-1471864190281-a93a3070b6de?auto=format&fit=crop&w=600&q=80"},
        {"title": "شمع عسل نحل طبيعي قطفة أولى (نصف كيلو)", "price": 170, "category": "شمع العسل", "badge": "طبيعي 100%", "desc": "إطارات شمع طبيعية مختومة خام بدون أي معالجة، تجربة تذوق ريفية أصيلة.", "image_url": "https://images.unsplash.com/photo-1587049352847-81a56d773cae?auto=format&fit=crop&w=600&q=80"},
    ],
    "portfolio": [
        {"title": "اختبار اختراق تطبيقات الويب والـ APIs (Web Pentest)", "price": 2500, "category": "خدمات الفحص الأمني", "badge": "شامل التقرير", "desc": "فحص أمني عميق وكشف ثغرات OWASP Top 10 و Business Logic مع تقديم تقرير تفصيلي بالحلول."},
        {"title": "تدقيق أمني للبنية التحتية والسيرفرات (Infra Audit)", "price": 3500, "category": "خدمات الفحص الأمني", "badge": "موصى به للشركات", "desc": "تقييم أمان الخوادم السحابية، جدران الحماية Firewall، وضبط تكوينات الحماية Hardening."},
        {"title": "استشارة أمنية وتقييم المخاطر السيبرانية (Consultation)", "price": 1000, "category": "استشارات وتوجيه", "badge": "فوري", "desc": "جلسة فنية لتحليل بنيتك الرقمية ووضع خطة تأمين متكاملة متوافقة مع المعايير القياسية."},
        {"title": "تأمين الحسابات ومكافحة الهندسة الاجتماعية (Hardening)", "price": 1200, "category": "حلول الحماية", "badge": "دعم فني", "desc": "تفعيل آليات 2FA/MFA، تدريب الفريق ضد رسائل التصيد Phishing، وتأمين البريد المؤسسي."},
    ],
    "restaurant": [
        {"title": "وجبة مشويات مشكلة مكس جريل (شخصين)", "price": 240, "category": "مشويات الفحم", "badge": "الأكثر طلباً", "desc": "كباب، كفتة بلدي، شيش طاووق، مع أرز بسمتي وسلطات وخبز.", "image_url": "https://images.unsplash.com/photo-1555939594-58d7cb561ad1?auto=format&fit=crop&w=600&q=80"},
        {"title": "طاجن ملوخية بالطشة واللحم البلدي", "price": 95, "category": "طواجن بلدي", "badge": "على أصوله", "desc": "ملوخية خضراء فريش بالسمن البلدي وقطع لحم كندوز فاخرة.", "image_url": "https://images.unsplash.com/photo-1546069901-ba9599a7e63c?auto=format&fit=crop&w=600&q=80"},
        {"title": "حواوشي بلدي سوبر بالجبنة الموتزاريلا", "price": 65, "category": "حواوشي ومخبوزات", "badge": "مقرمش وشهي", "desc": "لحم مفروم متبل بالخلطة السرية مع موتزاريلا سايحة.", "image_url": "https://images.unsplash.com/photo-1565299624946-b28f40a0ae38?auto=format&fit=crop&w=600&q=80"},
        {"title": "نصف دجاجة مشوية على الفحم + أرز مبهر", "price": 130, "category": "مشويات الفحم", "badge": "وجبة التوفير", "desc": "دجاج متبل بخلطة الأعشاب يقدم مع الأرز والبطاطس والتومية.", "image_url": "https://images.unsplash.com/photo-1598515214211-89d3c73ae83b?auto=format&fit=crop&w=600&q=80"},
        {"title": "سلطة طحينة وسلطة خضراء ومخلل مشكل", "price": 25, "category": "مقبلات وسلطات", "badge": "طازج", "desc": "تشكيلة سلطات شرقية طازجة تكمل وجبتك المفضلة.", "image_url": "https://images.unsplash.com/photo-1540420773420-3366772f4999?auto=format&fit=crop&w=600&q=80"},
    ],
    "vegetables": [
        {"title": "طماطم بلدي نخب أول (كيلو)", "price": 18, "category": "خضار طازج", "badge": "طازج اليوم", "desc": "طماطم سكرية مقطوفة صباحاً من مزارعنا بعناية فائقة.", "image_url": "https://images.unsplash.com/photo-1592924357228-91a4daadcfea?auto=format&fit=crop&w=600&q=80"},
        {"title": "بطاطس تحمير سبونتا (كيلو)", "price": 20, "category": "خضار طازج", "badge": "ممتاز للتحمير", "desc": "حبات بطاطس منتقاة بجودة عالية وخالية من الشوائب.", "image_url": "https://images.unsplash.com/photo-1518977676601-b53f82aba655?auto=format&fit=crop&w=600&q=80"},
        {"title": "خيار صوب بلدي فريش (كيلو)", "price": 16, "category": "خضار طازج", "badge": "الأكثر طلباً", "desc": "خيار مقرمش طازج يومياً مناسب للسلطات والاستهلاك اليومي.", "image_url": "https://images.unsplash.com/photo-1604977042946-1eecc30f269e?auto=format&fit=crop&w=600&q=80"},
        {"title": "بصل أحمر بلدي فاخر (كيلو)", "price": 22, "category": "خضار طازج", "badge": "جودة عالية", "desc": "بصل أحمر غني بالنكهة تخزين ممتاز.", "image_url": "https://images.unsplash.com/photo-1618512496248-a07fe83aa8cb?auto=format&fit=crop&w=600&q=80"},
        {"title": "بوكس التوفير العائلي المشكل (10 كجم)", "price": 195, "category": "بوكسات التوفير", "badge": "وفر 25%", "desc": "تشكيلة أسبوعية متكاملة (بطاطس، طماطم، بصل، خيار، كوسة، جزر).", "image_url": "https://images.unsplash.com/photo-1540420773420-3366772f4999?auto=format&fit=crop&w=600&q=80"},
        {"title": "موز بلدي سكري فاخر (كيلو)", "price": 28, "category": "فواكه موسمية", "badge": "حلاوة طبيعية", "desc": "موز بلدي كامل النضج غني بالطاقة والبوتاسيوم.", "image_url": "https://images.unsplash.com/photo-1571771894821-ce9b6c11b08e?auto=format&fit=crop&w=600&q=80"},
    ],
    "electronics": [
        {"title": "سماعة بلوتوث لاسلكية عازلة للضوضاء Pro", "price": 450, "category": "صوتيات وسماعات", "badge": "الأكثر مبيعاً", "desc": "صوت نقي بتقنية Hi-Fi مع مايك مدمج وبطارية تدوم 24 ساعة متواصلة.", "image_url": "https://images.unsplash.com/photo-1590658268037-6bf12165a8df?auto=format&fit=crop&w=600&q=80"},
        {"title": "ساعة ذكية مقاومة للماء مع تتبع نبضات القلب", "price": 680, "category": "إلكترونيات ذكية", "badge": "ضمان سنة", "desc": "شاشة أموليد لمسية، استقبال الإشعارات والمكالمات ومتابعة النشاط الرياضي.", "image_url": "https://images.unsplash.com/photo-1523275335684-37898b6baf30?auto=format&fit=crop&w=600&q=80"},
        {"title": "باور بانك شحن فائق السرعة 20,000 مللي أمبير", "price": 390, "category": "شواحن وبطاريات", "badge": "شحن سريع 22.5W", "desc": "منافذ Type-C و USB متعددة لشحن 3 أجهزة في وقت واحد بأمان تام.", "image_url": "https://images.unsplash.com/photo-1609592424109-dd9892f1b177?auto=format&fit=crop&w=600&q=80"},
        {"title": "شاحن جداري GaN ثلاثي المنافذ 65W للابتوب والموبايل", "price": 320, "category": "شواحن وبطاريات", "badge": "تقنية GaN", "desc": "شحن فائق السرعة متوافق مع الآيفون والسامسونج واللابتوب بحجم مدمج.", "image_url": "https://images.unsplash.com/photo-1583863788434-e58a36330cf0?auto=format&fit=crop&w=600&q=80"},
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
        {"title": "قميص كلاسيك أوكسفورد قطن مصري 100%", "price": 320, "category": "ملابس رجالي", "badge": "قطن مصري 100%", "desc": "خامة قطنية مريحة وناعمة، قصة سليم فيت عصرية مناسبة للعمل والمناسبات.", "image_url": "https://images.unsplash.com/photo-1596755094514-f87e34085b2c?auto=format&fit=crop&w=600&q=80"},
        {"title": "بنطلون جبردين إيطالي كلاسيك", "price": 380, "category": "ملابس رجالي", "badge": "الأكثر طلباً", "desc": "أقمشة إيطالية مستوردة عالية الجودة ومقاومة للانكماش بتفصيل متقن.", "image_url": "https://images.unsplash.com/photo-1624378439575-d8705ad7ae80?auto=format&fit=crop&w=600&q=80"},
        {"title": "سويت شيرت هودي أوفر سايز شتوي فاخر", "price": 420, "category": "كاجوال شتوي", "badge": "تريند 2026", "desc": "تقفيل فائق الجودة مع بطانة داخلية دافئة وخياطة مزدوجة فائقة المتانة.", "image_url": "https://images.unsplash.com/photo-1556905055-8f358a7a47b2?auto=format&fit=crop&w=600&q=80"},
        {"title": "تيشيرت بولو كاجوال قطن بيما ناعم", "price": 250, "category": "صيفي كاجوال", "badge": "قطن ناعم", "desc": "تيشيرت بولو أنيق بياقة متينة وملمس حريري يناسب الإطلالات اليومية.", "image_url": "https://images.unsplash.com/photo-1581655353564-df123a1eb820?auto=format&fit=crop&w=600&q=80"},
        {"title": "جاكيت جينز عصري أزرق غامق", "price": 550, "category": "ملابس خارجية", "badge": "خامة ممتازة", "desc": "تصميم كلاسيكي متين مع جيوب أمامية وأزرار معدنية غير قابلة للصدأ.", "image_url": "https://images.unsplash.com/photo-1576995853123-5a10305d93c0?auto=format&fit=crop&w=600&q=80"},
        {"title": "حذاء سنيكرز كاجوال جلد مريح", "price": 490, "category": "أحذية وإكسسوارات", "badge": "راحة فائقة", "desc": "نعل طبي مرن ومريح للمشي الطويل مع تصميم عصري يتماشى مع كافة الإطلالات.", "image_url": "https://images.unsplash.com/photo-1549298916-b41d501d3772?auto=format&fit=crop&w=600&q=80"},
    ],
    "general": [
        {"title": "الباقة الأساسية المتميزة", "price": 350, "category": "الخدمات الأساسية", "badge": "الأكثر طلباً", "desc": "خدمة متكاملة تشمل الفحص والمتابعة والدعم الفني الكامل.", "image_url": "https://images.unsplash.com/photo-1472851294608-062f824d29cc?auto=format&fit=crop&w=600&q=80"},
        {"title": "الباقة المتقدمة الاحترافية", "price": 750, "category": "باقات احترافية", "badge": "قيمة مضاعفة", "desc": "تشمل كافة المميزات مع أولوية التنفيذ وتوصيل مجاني.", "image_url": "https://images.unsplash.com/photo-1441986300917-64674bd600d8?auto=format&fit=crop&w=600&q=80"},
        {"title": "الخدمة السريعة الفورية", "price": 150, "category": "خدمات سريعة", "badge": "فوري", "desc": "تنفيذ عاجل خلال ساعات معدودة بأعلى معايير الدقة.", "image_url": "https://images.unsplash.com/photo-1526170375885-4d8ecf77b99f?auto=format&fit=crop&w=600&q=80"},
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
        document = build_portfolio_html(job_id, client, request, settings, items)
    else:
        document = build_store_html(job_id, client, request, settings, items, niche)

    issues = artifacts.validate_site_html(document)
    if issues:
        raise RuntimeError("Generated template failed artifact validation: " + "; ".join(issues))
    return document


def build_portfolio_html(job_id: int, client: str, request: str, settings: dict = None, items: list = None) -> str:
    """Generates an elite dark-mode Cybersecurity & Tech Portfolio SPA."""
    settings = settings or {}
    items = items or []
    
    # Extract candidate name
    brand_name = _safe_text(settings.get("brand_name") or client, "ياسين أحمد | Yaseen Ahmed", 120)
    if brand_name.startswith("tg:"):
        brand_name = "ياسين أحمد | Yaseen Ahmed"
        
    slogan = _safe_text(settings.get("slogan"), "خبير الأمن السيبراني واختبار الاختراق وتأمين الأنظمة السحابية", 500)
    
    pal = PALETTES["cyber"]
    primary = _safe_hex_color(settings.get("color_primary"), pal["primary"])
    secondary = _safe_hex_color(settings.get("color_secondary"), pal["secondary"])
    accent = pal["accent"]
    
    phone = _safe_phone(settings.get("phone"))
    whatsapp = _safe_phone(settings.get("whatsapp"), phone)
    clean_wa = re.sub(r"[^\d]", "", whatsapp)
    if clean_wa.startswith("01"):
        clean_wa = "2" + clean_wa
    if clean_wa:
        portfolio_contact_cta = f'''<a href="https://wa.me/{clean_wa}?text={html.escape('مرحباً ' + brand_name + '، أود مناقشة مشروع.')}" target="_blank" rel="noopener" class="px-8 py-3.5 rounded-xl bg-slate-900 border border-slate-700 hover:border-cyan-500 text-white font-bold text-sm transition">
            💬 محادثة واتساب مباشرة
          </a>'''
        portfolio_footer_contact = f'''<a href="https://wa.me/{clean_wa}" target="_blank" rel="noopener" class="hover:text-cyan-400 font-bold">📲 WhatsApp: {html.escape(whatsapp)}</a>'''
    else:
        portfolio_contact_cta = '''<span class="px-8 py-3.5 rounded-xl bg-slate-800 border border-slate-700 text-slate-300 font-bold text-sm">بيانات التواصل قيد الإعداد</span>'''
        portfolio_footer_contact = '''<span class="font-bold">بيانات التواصل قيد الإعداد</span>'''

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

    items_json = _json_for_script(items)

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
  <a href="#main-content" class="sr-only focus:not-sr-only focus:fixed focus:top-3 focus:left-3 focus:z-[100] focus:rounded-lg focus:bg-white focus:px-4 focus:py-3 focus:text-slate-950">تخطي إلى المحتوى الرئيسي / Skip to main content</a>

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

  <main id="main-content" tabindex="-1">
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
        {portfolio_contact_cta}
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
            <h4 class="font-bold text-white text-base mb-2">{html.escape(str(it.get("title") or ""))}</h4>
            <p class="text-xs text-slate-400 font-readex leading-relaxed mb-6">{html.escape(str(it.get("description") or ""))}</p>
          </div>
          <div>
            <div class="text-xl font-black text-cyan-400 font-mono mb-4">{_safe_price(it.get("price"))} ج.م</div>
            <button onclick="requestService({_inline_js_value(it.get("title") or "")}, {_safe_price(it.get("price"))})" class="w-full py-2.5 rounded-xl bg-cyan-500/20 hover:bg-cyan-500 text-cyan-300 hover:text-slate-950 border border-cyan-500/40 font-bold text-xs transition">
              🛡️ طلب الخدمة والتعاقد
            </button>
          </div>
        </div>
        ''' for it in items)}
      </div>
    </div>
  </section>

  <!-- Contact & Footer -->
  </main>
  <footer id="contact" class="py-12 bg-slate-950 border-t border-slate-900 text-xs">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between gap-6">
      <div>
        <p class="font-bold text-white text-sm mb-1">{html.escape(brand_name)}</p>
        <p class="text-slate-500 font-readex">جميع الحقوق محفوظة © 2026 — مصمم ومنشور عبر وكالة AutoCorp الذاتية</p>
      </div>
      <div class="flex items-center gap-4 text-slate-300">
        {portfolio_footer_contact}
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
          headers: {{ 'Content-Type': 'application/json', 'Idempotency-Key': crypto.randomUUID() }},
          body: JSON.stringify(payload)
        }});
        const d = await res.json().catch(() => ({{}}));
        if (!res.ok) throw new Error(d.detail || 'Unable to submit the service request.');
        closeHireModal();
        const msg = encodeURIComponent(`مرحباً {html.escape(brand_name)} 👋\\nأود التعاقد على خدمة: ${{payload.items[0].title}}\\nالاسم: ${{payload.customer_name}}\\nالهاتف: ${{payload.customer_phone}}`);
        if (WA_NUMBER) {{
          alert('✅ تم استلام طلبك بنجاح! سيتم فتح واتساب للتأكيد المباشر.');
          window.open(`https://wa.me/${{WA_NUMBER}}?text=${{msg}}`, '_blank', 'noopener');
        }} else {{
          alert('✅ تم استلام طلبك بنجاح. بيانات التواصل قيد الإعداد.');
        }}
      }} catch(err) {{
        alert('تعذر إرسال الطلب. يرجى المحاولة مرة أخرى.');
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
    brand_name = _safe_text(settings.get("brand_name") or client, "خضار فريش" if niche == "vegetables" else "مناحل الشفاء" if niche == "honey" else "المتجر المصري", 120)
    if brand_name.startswith("tg:"):
        brand_name = "مناحل الشفاء للعسل الطبيعي" if niche == "honey" else "متجر الخضار الطازج" if niche == "vegetables" else "المتجر الإلكتروني"
        
    slogan = _safe_text(settings.get("slogan"), (
        "عسل سدر جبلي وطبيعي 100% مفحوص معملياً من المنحل لباب بيتك" if niche == "honey"
        else "خضارك طازج من المزرعة لباب بيتك بأعلى جودة وأفضل سعر في مصر" if niche == "vegetables" 
        else "أشهى المأكولات والمشويات على أصولها بتوصيل سريع وساخن" if niche == "restaurant"
        else "أحدث الأجهزة والإلكترونيات الذكية بأفضل الأسعار وضمان حقيقي" if niche == "electronics"
        else "خدمات احترافية متكاملة تلبي احتياجاتك بأعلى معايير الجودة"
    ), 500)
    
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
        contact_actions = f'''<a href="https://wa.me/{clean_wa}?text={html.escape('مرحباً ' + brand_name + '، أريد التحدث مع خدمة العملاء.')}" target="_blank" rel="noopener" class="px-8 py-3.5 rounded-xl bg-emerald-500 hover:bg-emerald-600 text-white font-black text-center text-sm shadow-lg transition">
            📲 تحدث واتساب الآن
          </a>'''
        promo_contact_cta = f'''<a href="https://wa.me/{clean_wa}?text={html.escape('مرحباً، أريد الاستفسار عن عروض ' + brand_name)}" target="_blank" rel="noopener" class="text-amber-400 hover:underline font-bold mr-2">طلب واتساب مباشر</a>'''
        hero_contact_cta = f'''<a href="https://wa.me/{clean_wa}?text={html.escape('مرحباً، أود التواصل مع إدارة ' + brand_name)}" target="_blank" rel="noopener" class="px-8 py-3.5 rounded-xl bg-white/15 backdrop-blur text-white border border-white/30 font-bold text-sm hover:bg-white/25 transition">💬 محادثة واتساب سريعة</a>'''
    else:
        contact_actions = '''<span class="px-8 py-3.5 rounded-xl bg-white/10 border border-white/20 text-slate-300 font-bold text-center text-sm">بيانات التواصل قيد الإعداد</span>'''
        promo_contact_cta = '''<a href="#contact" class="text-amber-400 hover:underline font-bold mr-2">بيانات التواصل قيد الإعداد</a>'''
        hero_contact_cta = '''<a href="#contact" class="px-8 py-3.5 rounded-xl bg-white/15 backdrop-blur text-white border border-white/30 font-bold text-sm hover:bg-white/25 transition">💬 بيانات التواصل قيد الإعداد</a>'''
        
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
        f'<button onclick="filterCategory({_inline_js_value(c)})" class="cat-btn px-4 py-2 rounded-xl text-xs font-bold transition bg-white text-slate-600 border border-slate-200 hover:bg-slate-100" data-cat="{html.escape(str(c))}">{html.escape(str(c))}</button>'
        for c in categories
    )
    
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
            <h1 class="text-xl sm:text-2xl font-black text-slate-900 leading-tight">{html.escape(brand_name)}</h1>
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
      <h2 class="text-3xl sm:text-5xl lg:text-6xl font-black leading-tight max-w-4xl mx-auto mb-6">
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
      
      <!-- Category Filter Tabs -->
      <div class="flex flex-wrap gap-2" id="category-filters">
        <button onclick="filterCategory('الكل')" class="cat-btn px-4 py-2 rounded-xl text-xs font-bold transition bg-slate-900 text-white" data-cat="الكل" data-i18n="cat_all">الكل</button>
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
        <span class="text-xs font-bold text-amber-600 tracking-wider uppercase font-readex" data-i18n="reviews_badge">تقييمات موثقة</span>
        <h3 class="text-2xl sm:text-3xl font-black text-slate-900 mt-1" data-i18n="reviews_title">آراء وتجارب العملاء ⭐⭐⭐⭐⭐</h3>
      </div>
      <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div class="p-6 rounded-2xl bg-white border border-slate-200 shadow-sm">
          <div class="flex items-center justify-between mb-2">
            <b class="text-xs text-slate-900">محمد السعيد</b>
            <span class="text-amber-400 text-xs">★★★★★</span>
          </div>
          <p class="text-xs text-slate-600 font-readex leading-relaxed" data-i18n="rev1_text">
            المنتجات وصلت مطابقة للصور تماماً، وسرعة الاستجابة على الواتساب والتوصيل محترمة جداً.
          </p>
        </div>
        <div class="p-6 rounded-2xl bg-white border border-slate-200 shadow-sm">
          <div class="flex items-center justify-between mb-2">
            <b class="text-xs text-slate-900">سارة إبراهيم</b>
            <span class="text-amber-400 text-xs">★★★★★</span>
          </div>
          <p class="text-xs text-slate-600 font-readex leading-relaxed" data-i18n="rev2_text">
            التغليف فاخر وأصلي والدفع بإنستاباي كان في ثواني، شكراً على الأمانة والاحترافية.
          </p>
        </div>
        <div class="p-6 rounded-2xl bg-white border border-slate-200 shadow-sm">
          <div class="flex items-center justify-between mb-2">
            <b class="text-xs text-slate-900">أحمد حسام</b>
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
          <p class="text-slate-300 text-sm font-readex max-w-xl">
            فريق خدمة عملاء {html.escape(brand_name)} جاهز للرد على استفساراتكم ومتابعة طلباتكم على مدار الساعة.
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
          {f'''<a href="tel:{phone}" class="px-8 py-3.5 rounded-xl bg-white/10 hover:bg-white/20 border border-white/20 text-white font-bold text-center text-sm transition">📞 اتصل هاتفياً</a>''' if phone else ''}
        </div>
      </div>
    </div>
  </section>

  <!-- Footer -->
  </main>
  <footer class="bg-slate-950 text-slate-400 py-8 border-t border-slate-800 text-xs">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between gap-4">
      <div>
        <p>© 2026 <b>{html.escape(brand_name)}</b> — <span data-i18n="footer_rights">جميع الحقوق محفوظة.</span></p>
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
    <div class="bg-white rounded-3xl max-w-lg w-full max-h-[90vh] overflow-y-auto p-6 sm:p-8 shadow-2xl relative">
      <div class="flex items-center justify-between pb-4 mb-4 border-b border-slate-100">
        <div>
          <h3 class="text-xl font-black text-slate-900" data-i18n="checkout_modal_title">إرسال طلب إلى التاجر 🇪🇬</h3>
          <p class="text-xs text-slate-500 font-readex" data-i18n="checkout_modal_sub">سيتواصل التاجر لتأكيد الطلب وطريقة الدفع؛ لا تُعالج أي دفعة هنا.</p>
        </div>
        <button onclick="closeCheckoutModal()" class="w-8 h-8 rounded-full bg-slate-100 text-slate-500 hover:bg-slate-200 flex items-center justify-center font-bold">✕</button>
      </div>

      <form id="order-form" onsubmit="submitOrder(event)" class="space-y-4">
        <div>
          <label class="block text-xs font-bold text-slate-700 mb-1" data-i18n="checkout_name_lbl">الاسم بالكامل *</label>
          <input type="text" id="cust-name" required data-i18n="checkout_name_ph" placeholder="مثال: أحمد محمود" class="w-full px-3.5 py-2.5 rounded-xl border border-slate-300 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500">
        </div>
        <div>
          <label class="block text-xs font-bold text-slate-700 mb-1" data-i18n="checkout_phone_lbl">رقم الهاتف / الواتساب *</label>
          <input type="tel" id="cust-phone" required data-i18n="checkout_phone_ph" placeholder="مثال: 01012345678" class="w-full px-3.5 py-2.5 rounded-xl border border-slate-300 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500">
        </div>
        <div>
          <label class="block text-xs font-bold text-slate-700 mb-1" data-i18n="checkout_address_lbl">عنوان التوصيل بالتفصيل *</label>
          <textarea id="cust-address" required data-i18n="checkout_address_ph" placeholder="المدينة، الحي، اسم الشارع، رقم العمارة والشقة" class="w-full px-3.5 py-2 rounded-xl border border-slate-300 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500" rows="2"></textarea>
        </div>

        <!-- The prototype records an order request only; it must not direct a
             customer to an unverified wallet or payment provider. -->
        <div>
          <label class="block text-xs font-bold text-slate-700 mb-2" data-i18n="checkout_payment_lbl">حالة الدفع</label>
          <div class="text-xs font-bold">
            <label class="flex items-center gap-2 p-3 rounded-xl border border-slate-200 cursor-pointer hover:bg-slate-50 transition">
              <input type="radio" name="pay_method" value="cash_on_delivery" checked class="text-brand-500">
              <div>
                <div data-i18n="checkout_payment_opt">بانتظار تأكيد التاجر</div>
                <div class="text-[10px] text-slate-400 font-normal" data-i18n="checkout_payment_desc">سيحدد التاجر طريقة الدفع والتسليم بعد مراجعة الطلب.</div>
              </div>
            </label>
          </div>
        </div>

        <button type="submit" id="submit-order-btn" data-i18n="checkout_submit_btn" class="w-full py-3.5 rounded-xl font-black text-white text-sm shadow-lg transition mt-4" style="background:{primary}">
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
      <h3 class="text-xl font-black text-slate-900 mb-1" data-i18n="success_modal_title">تم تأكيد طلبك بنجاح! 🎉</h3>
      <p class="text-xs text-slate-500 font-readex mb-6" data-i18n="success_modal_sub">شكراً لاختيارك {html.escape(brand_name)}. جاري تجهيز طلبك للشحن والتسليم فوراً.</p>

      <div class="bg-slate-50 rounded-2xl p-4 text-xs font-readex space-y-2 mb-6 border border-slate-100 text-right">
        <div class="flex justify-between">
          <span class="text-slate-500" data-i18n="success_order_id_lbl">رقم الأوردر:</span>
          <b id="res-order-id" class="text-slate-900 font-mono">#0000</b>
        </div>
        <div class="flex justify-between">
          <span class="text-slate-500" data-i18n="success_total_lbl">إجمالي المبلغ:</span>
          <b id="res-total" class="text-emerald-600 font-black">0 ج.م</b>
        </div>
        <div class="flex justify-between">
          <span class="text-slate-500" data-i18n="success_method_lbl">طريقة الدفع:</span>
          <b id="res-payment-method" class="text-slate-800">كاش</b>
        </div>
        <div class="flex justify-between">
          <span class="text-slate-500" data-i18n="success_ref_lbl">المرجع / الكود:</span>
          <b id="res-payment-ref" class="text-slate-800 font-mono">COD-0000</b>
        </div>
      </div>

      <div class="space-y-3">
        <a id="res-whatsapp-link" href="#" target="_blank" data-i18n="success_wa_btn" class="block w-full py-3 rounded-xl bg-emerald-500 hover:bg-emerald-600 text-white font-bold text-xs shadow-md transition">
          💬 إرسال تفاصيل الأوردر للواتساب للتأكيد
        </a>
        <button onclick="closeSuccessModal()" data-i18n="success_close_btn" class="w-full py-3 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 font-bold text-xs transition">
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

    function escapeProductHtml(value) {{
      return String(value ?? '').replace(/[&<>"']/g, char => {{
        return {{ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }}[char];
      }});
    }}

    function renderProducts() {{
      const grid = document.getElementById('products-grid');
      const dict = (typeof I18N !== 'undefined' && I18N[storeLang]) ? I18N[storeLang] : {{"empty_cat": "لا توجد منتجات في هذا القسم حالياً", "add_to_cart": "+ أضف للسلة", "price_lbl": "السعر:", "currency": "ج.م"}};
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
        const category = escapeProductHtml(p.category);
        const badge = escapeProductHtml(p.badge);
        const title = escapeProductHtml(p.title);
        const description = escapeProductHtml(p.description || (storeLang === 'en' ? 'Certified high-quality item.' : 'صنف عالي الجودة ومضمون تم اختياره بعناية.'));
        const imageUrl = p.image_url ? escapeProductHtml(p.image_url) : '';
        const addBtnText = dict.add_to_cart;
        const priceLabel = dict.price_lbl;
        const curr = dict.currency;
        return `
        <div class="bg-white rounded-3xl border border-slate-200/80 p-5 shadow-sm hover:shadow-xl transition-all duration-300 flex flex-col justify-between group hover:-translate-y-1">
          <div>
            ${{imageUrl ? `
            <div class="overflow-hidden rounded-2xl mb-4 bg-slate-100 aspect-square flex items-center justify-center">
              <img src="${{imageUrl}}" alt="${{title}}" class="w-full h-full object-cover group-hover:scale-105 transition duration-500" loading="lazy" onerror="this.onerror=null;this.parentElement.innerHTML='<div class=\\'w-full h-full flex items-center justify-center text-4xl bg-slate-100\\'>🛍️</div>';">
            </div>` : `
            <div class="overflow-hidden rounded-2xl mb-4 bg-gradient-to-br from-slate-100 to-slate-200 aspect-square flex items-center justify-center text-4xl">
              🛍️
            </div>`}}
            <div class="flex items-center justify-between mb-3">
              <span class="text-[11px] font-bold px-2.5 py-1 rounded-full bg-slate-100 text-slate-600 font-readex">
                ${{category}}
              </span>
              ${{badge ? `<span class="text-[11px] font-black px-2.5 py-1 rounded-full text-brand-600" style="background:${pal["badge_bg"]};color:${pal["badge_text"]}">★ ${{badge}}</span>` : ''}}
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
              <div class="text-lg font-black text-slate-900">${{safePrice}} <span class="text-xs font-bold text-slate-500">${{curr}}</span></div>
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
      const dict = (typeof I18N !== 'undefined' && I18N[storeLang]) ? I18N[storeLang] : {{
        "cart_items_count": "عناصر",
        "cart_empty_title": "سلتك فارغة حالياً",
        "cart_empty_sub": "تصفح القائمة وأضف منتجاتك المفضلة",
        "currency": "ج.م"
      }};
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
        const itemTitle = escapeProductHtml(p.title);
        const rawPrice = Number(p.price);
        const itemPrice = Number.isFinite(rawPrice) && rawPrice >= 0 ? rawPrice : 0;
        const lineTotal = itemPrice * cart[id];
        subtotal += lineTotal;
        return `
          <div class="flex items-center justify-between p-3.5 rounded-2xl bg-slate-50 border border-slate-100">
            <div class="flex-1 min-w-0 pr-2">
              <h5 class="text-xs font-black text-slate-900 truncate">${{itemTitle}}</h5>
              <div class="text-[11px] text-slate-500">${{itemPrice}} ${{dict.currency}} × ${{cart[id]}}</div>
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
      if (subtotalEl) subtotalEl.textContent = subtotal + ' ' + dict.currency;
      const shippingEl = document.getElementById('cart-shipping');
      if (shippingEl) shippingEl.textContent = shipping + ' ' + dict.currency;
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
      if (totalEl) totalEl.textContent = Math.max(0, (subtotal - discountVal + shipping)).toFixed(0) + ' ' + dict.currency;
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

    const I18N = {{
      ar: {{
        promo_bar_text: '🎉 <b>عروض حصرية:</b> كود خصم 10%: <b>WELCOME10</b> | 🚚 توصيل سريع لجميع المحافظات',
        brand_sub: 'المتجر الإلكتروني المعتمد 🇪🇬',
        nav_home: 'الرئيسية',
        nav_catalog: 'المنتجات',
        nav_features: 'المميزات',
        nav_reviews: 'آراء العملاء',
        nav_contact: 'تواصل معنا',
        theme_dark: 'ليلي',
        theme_light: 'نهاري',
        lang_btn: 'English',
        cart_btn: 'السلة',
        hero_badge: 'منتجات مصرية أصلية 100%',
        hero_cta: '🛍️ تصفح التشكيلة واطلب فوراً',
        feat1_title: 'خامات قطنية ممتازة',
        feat1_desc: 'أعلى معايير الجودة والتصنيع المصري الفاخر.',
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
        rev1_text: 'المنتجات وصلت مطابقة للصور تماماً، وسرعة الاستجابة على الواتساب والتوصيل محترمة جداً.',
        rev2_text: 'التغليف فاخر وأصلي والدفع بإنستاباي كان في ثواني، شكراً على الأمانة والاحترافية.',
        rev3_text: 'أفضل تجربة شراء أونلاين في مصر، بالتأكيد هكرر الطلب تاني.',
        contact_badge: 'خدمة العملاء متصلة',
        contact_title: 'هل لديك استفسار أو طلب خاص؟',
        contact_phone_lbl: 'هاتف:',
        contact_wa_lbl: 'واتساب:',
        contact_addr_lbl: 'العنوان:',
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
        success_order_id_lbl: 'رقم الأوردر:',
        success_total_lbl: 'إجمالي المبلغ:',
        success_method_lbl: 'طريقة الدفع:',
        success_ref_lbl: 'المرجع / الكود:',
        success_wa_btn: '💬 إرسال تفاصيل الأوردر للواتساب للتأكيد',
        success_close_btn: 'إغلاق ومتابعة التسوق'
      }},
      en: {{
        promo_bar_text: '🎉 <b>Exclusive Deals:</b> 10% Off Code: <b>WELCOME10</b> | 🚚 Fast Delivery Nationwide',
        brand_sub: 'Certified Online Store 🇪🇬',
        nav_home: 'Home',
        nav_catalog: 'Catalog',
        nav_features: 'Features',
        nav_reviews: 'Reviews',
        nav_contact: 'Contact',
        theme_dark: 'Dark',
        theme_light: 'Light',
        lang_btn: 'العربية',
        cart_btn: 'Cart',
        hero_badge: '100% Egyptian Authentic Quality',
        hero_cta: '🛍️ Browse Catalog & Order',
        feat1_title: 'Premium Egyptian Fabric',
        feat1_desc: 'Finest authentic quality crafted to perfection.',
        feat2_title: 'Direct Fast Delivery',
        feat2_desc: 'Express door-to-door delivery across all governorates.',
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
        rev1_text: 'Products arrived exactly as pictured, fast WhatsApp response and great delivery.',
        rev2_text: 'Luxury packaging, InstaPay payment took seconds, thank you for the professionalism.',
        rev3_text: 'Best online shopping experience in Egypt, will definitely order again.',
        contact_badge: 'Customer Support Online',
        contact_title: 'Have a Question or Special Request?',
        contact_phone_lbl: 'Phone:',
        contact_wa_lbl: 'WhatsApp:',
        contact_addr_lbl: 'Address:',
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
        success_order_id_lbl: 'Order ID:',
        success_total_lbl: 'Total Amount:',
        success_method_lbl: 'Payment Method:',
        success_ref_lbl: 'Reference / Code:',
        success_wa_btn: '💬 Send Order Details via WhatsApp',
        success_close_btn: 'Close & Continue Shopping'
      }}
    }};

    let isStoreDark = false;
    function applyStoreTheme(dark) {{
      isStoreDark = !!dark;
      if (isStoreDark) {{
        document.documentElement.classList.add('dark');
      }} else {{
        document.documentElement.classList.remove('dark');
      }}
      try {{ localStorage.setItem('store_theme', isStoreDark ? 'dark' : 'light'); }} catch (e) {{}}
      const lbl = document.getElementById('store-theme-lbl');
      if (lbl) {{
        const dict = (typeof I18N !== 'undefined' && I18N[storeLang]) ? I18N[storeLang] : I18N.ar;
        lbl.textContent = isStoreDark ? dict.theme_dark : dict.theme_light;
      }}
    }}

    function toggleStoreTheme() {{
      applyStoreTheme(!isStoreDark);
    }}

    let storeLang = 'ar';
    function applyStoreLang(lang) {{
      storeLang = (lang === 'en') ? 'en' : 'ar';
      document.documentElement.lang = storeLang;
      document.documentElement.dir = (storeLang === 'ar') ? 'rtl' : 'ltr';
      try {{ localStorage.setItem('store_lang', storeLang); }} catch (e) {{}}

      const dict = (typeof I18N !== 'undefined' && I18N[storeLang]) ? I18N[storeLang] : I18N.ar;

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

      renderProducts();
      updateCartUI();
    }}

    function toggleStoreLang() {{
      applyStoreLang(storeLang === 'ar' ? 'en' : 'ar');
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
        document.getElementById('res-total').textContent = (result.total_egp ?? total) + ' ج.م';
        document.getElementById('res-payment-method').textContent = 'بانتظار تأكيد التاجر';
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
          confirmationLink.textContent = 'بيانات التواصل قيد الإعداد';
        }}
        
        document.getElementById('success-modal').classList.remove('hidden');
      }} catch (err) {{
        alert('حدث خطأ أثناء إرسال الطلب: ' + err.message);
      }} finally {{
        btn.disabled = false;
        btn.textContent = '✅ تأكيد وإرسال الطلب الآن';
      }}
    }}

    // Init
    try {{
      const savedTheme = localStorage.getItem('store_theme');
      const prefersDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
      applyStoreTheme(savedTheme ? savedTheme === 'dark' : prefersDark);
    }} catch (e) {{
      applyStoreTheme(false);
    }}

    try {{
      const savedLang = localStorage.getItem('store_lang') || 'ar';
      applyStoreLang(savedLang);
    }} catch (e) {{
      renderProducts();
      updateCartUI();
    }}
  </script>
</body>
</html>"""
    return html_code
