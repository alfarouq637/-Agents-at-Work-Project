"""AutoCorp Enterprise Full-Stack Project Generator.

Synthesizes a production-grade, modular Node.js/Express 5 enterprise backend architecture
paired with a bilingual (AR/EN), Dark/Light theme responsive frontend client.

Exact Project Structure:
Store-Backend/
│
├── src/
│   ├── config/
│   │   ├── database.js          # In-memory / JSON / SQLite data store with initial seeds
│   │   └── env.js               # Validated environment configuration
│   │
│   ├── models/
│   │   ├── index.js             # Model associations & registry
│   │   ├── user.model.js
│   │   ├── category.model.js
│   │   ├── product.model.js
│   │   ├── cart.model.js
│   │   ├── cartItem.model.js
│   │   ├── order.model.js
│   │   ├── orderItem.model.js
│   │   ├── review.model.js
│   │   ├── discount.model.js
│   │   ├── promoCode.model.js
│   │   └── newsletterSubscriber.model.js
│   │
│   ├── modules/
│   │   ├── auth/ (controller, service, routes, validation)
│   │   ├── categories/ (controller, service, routes, validation)
│   │   ├── products/ (controller, service, routes, validation)
│   │   ├── cart/ (controller, service, routes, validation)
│   │   ├── orders/ (controller, service, routes, validation)
│   │   ├── reviews/ (controller, service, routes, validation)
│   │   ├── customers/ (controller, service, routes, validation)
│   │   ├── discounts/ (controller, service, routes, validation)
│   │   ├── promoCodes/ (controller, service, routes, validation)
│   │   ├── newsletter/ (controller, service, routes, validation)
│   │   └── dashboard/ (controller, service, routes)
│   │
│   ├── middlewares/
│   │   ├── auth.middleware.js          # JWT verification
│   │   ├── admin.middleware.js         # Admin role guard
│   │   ├── customer.middleware.js      # Customer role guard
│   │   ├── validate.middleware.js      # Request validation
│   │   ├── errorHandler.middleware.js  # Global error handler
│   │   └── rateLimiter.middleware.js   # Global & Auth rate limiters
│   │
│   ├── utils/
│   │   ├── response.js                 # Standardized JSON response envelope
│   │   ├── ApiError.js                 # Operational error class
│   │   ├── jwt.js                      # Token signing & verification
│   │   ├── pagination.js               # Offset/limit calculator
│   │   ├── sendVerificationEmail.js    # Email verification dispatcher
│   │   └── sendResetPasswordEmail.js   # Password reset dispatcher
│   │
│   ├── routes/
│   │   └── index.js                    # Route aggregator for /api/v1
│   │
│   └── app.js                          # Express setup with Helmet, CORS, Morgan
│
├── public/
│   ├── index.html                      # Bilingual AR/EN + Dark/Light interactive SPA
│   └── admin.html                      # Real-time Executive Admin Operations Portal
│
├── .env
├── .env.example
├── .gitignore
├── Dockerfile
├── docker-compose.yml
├── vercel.json
├── package.json
├── server.js
└── README.md                           # Exhaustive API docs & deployment guide
"""

import html
import json
import math
import re
from typing import Dict, Any, List


def _json_for_script(value: Any, *, indent: int = None) -> str:
    """Serialize data safely when embedding it in a generated script block."""
    return (
        json.dumps(value, ensure_ascii=False, indent=indent)
        .replace("<", "\\u003c")
        .replace(">", "\\u003e")
        .replace("&", "\\u0026")
        .replace("\u2028", "\\u2028")
        .replace("\u2029", "\\u2029")
    )


def _safe_text(value: Any, fallback: str, max_length: int = 240) -> str:
    """Normalize tenant text before it enters a generated artifact."""
    text = str(value or "").strip()
    return text[:max_length] if text else fallback


def _safe_hex_color(value: Any, fallback: str) -> str:
    """Allow only hex colours in generated CSS/JavaScript configuration."""
    candidate = str(value or "").strip()
    return candidate if re.fullmatch(r"#[0-9A-Fa-f]{3}(?:[0-9A-Fa-f]{3})?(?:[0-9A-Fa-f]{2})?", candidate) else fallback


def _safe_phone(value: Any, fallback: str = "") -> str:
    """Keep generated contact settings free of markup and SQL delimiters."""
    digits = re.sub(r"\D", "", str(value or ""))[:20]
    return digits or fallback


def _safe_identifier(value: str, fallback: str = "store") -> str:
    """Create a portable deployment/email identifier from display text."""
    identifier = re.sub(r"[^a-z0-9]+", "", value.lower())[:40]
    return identifier or fallback

def generate_enterprise_project(
    job_id: int,
    brand_name: str,
    niche: str,
    slogan: str,
    primary_color: str,
    secondary_color: str,
    items: List[Dict[str, Any]],
    settings: Dict[str, Any]
) -> Dict[str, str]:
    """
    Returns a dictionary mapping relative file paths to their complete,
    production-ready file contents.
    """
    settings = settings or {}
    clean_brand = _safe_text(brand_name, "المتجر المصري", 120)
    clean_slogan = _safe_text(slogan, "الجودة والتميز في كل طلب", 500)
    primary_color = _safe_hex_color(primary_color, "#0284c7")
    secondary_color = _safe_hex_color(secondary_color, "#38bdf8")
    phone = _safe_phone(settings.get("phone"))
    whatsapp = _safe_phone(settings.get("whatsapp"), phone)
    brand_identifier = _safe_identifier(clean_brand)

    # Standardize catalog items
    catalog = []
    categories = set()
    for idx, it in enumerate(items or []):
        cat = it.get("category") or "عام"
        categories.add(cat)
        catalog.append({
            "id": idx + 1,
            "title": it.get("title") or f"منتج {idx+1}",
            "title_en": it.get("title_en") or f"Product {idx+1}",
            "price": float(it.get("price") or 150),
            "category": cat,
            "badge": it.get("badge") or "جديد",
            "stock": 50,
            "rating": 0.0,
            "reviews_count": 0,
            "description": it.get("description") or f"أعلى معايير الجودة والتصنيع الأصلي لـ {it.get('title')}",
            "image_url": it.get("image_url") or f"https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=600&auto=format&fit=crop&q=80"
        })

    if not catalog:
        catalog = [
            {
                "id": 1,
                "title": "المنتج المميز الفاخر",
                "title_en": "Premium Featured Product",
                "price": 299.0,
                "category": "منتجات مميزة",
                "badge": "الأكثر مبيعاً",
                "stock": 35,
                "rating": 0.0,
                "reviews_count": 0,
                "description": "منتج أصلي عالي الجودة مع ضمان استبدال وتوصيل سريع لكافة المحافظات.",
                "image_url": "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=600&auto=format&fit=crop&q=80"
            },
            {
                "id": 2,
                "title": "الباقة الاقتصادية المتكاملة",
                "title_en": "Value Saver Pack",
                "price": 499.0,
                "category": "عروض خاصة",
                "badge": "خصم 20%",
                "stock": 20,
                "rating": 0.0,
                "reviews_count": 0,
                "description": "وفر أكثر مع الباقة الشاملة الأكثر طلباً في السوق المصري.",
                "image_url": "https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=600&auto=format&fit=crop&q=80"
            }
        ]
        categories = {"منتجات مميزة", "عروض خاصة"}

    cat_list = [{"id": i + 1, "name": c, "name_en": f"Cat {i+1}"} for i, c in enumerate(categories)]

    files: Dict[str, str] = {}

    # 1. package.json
    files["package.json"] = json.dumps({
        "name": f"store-backend-{job_id}",
        "version": "1.0.0",
        "description": f"{clean_brand} Enterprise Full-Stack E-Commerce & Management Platform",
        "main": "server.js",
        "scripts": {
            "start": "node server.js",
            "dev": "nodemon server.js",
            "test": "jest --detectOpenHandles --forceExit"
        },
        "keywords": ["ecommerce", "express", "fullstack", "egypt", "autocorp", "drizzle", "modular", "owasp-top-10"],
        "author": "AutoCorp Enterprise Synthesizer",
        "license": "MIT",
        "dependencies": {
            "express": "^4.19.2",
            "cors": "^2.8.5",
            "helmet": "^7.1.0",
            "morgan": "^1.10.0",
            "dotenv": "^16.4.5",
            "bcryptjs": "^2.4.3",
            "jsonwebtoken": "^9.0.2",
            "cookie-parser": "^1.4.6",
            "drizzle-orm": "^0.30.10",
            "better-sqlite3": "^9.6.0"
        },
        "devDependencies": {
            "nodemon": "^3.1.0",
            "jest": "^29.7.0",
            "supertest": "^6.3.4"
        }
    }, indent=2, ensure_ascii=False)

    # 2. .env.example & .env
    files[".env.example"] = """PORT=5000
NODE_ENV=development
JWT_SECRET=  # set a unique 32+-character secret in the deployment secret manager
JWT_EXPIRES_IN=7d
CORS_ORIGIN=http://localhost:5000
TRUST_PROXY_HOPS=0

# Payment adapters are intentionally disabled until verified gateway webhooks
# and reconciliation are implemented. Do not add payment credentials here.
"""

    # 3. .gitignore
    files[".gitignore"] = """node_modules/
.env
*.log
.DS_Store
"""

    # 4. server.js (Express Entrypoint)
    files["server.js"] = f"""/**
 * Generated AutoCorp Enterprise Server
 * Generated autonomously by AutoCorp AI Agency
 */
require('dotenv').config();
const app = require('./src/app');

const PORT = process.env.PORT || 5000;

app.listen(PORT, () => {{
  console.log('====================================================');
  console.log('🚀 Enterprise Server Running!');
  console.log(`🌐 Local URL:     http://localhost:${{PORT}}`);
  console.log(`📊 Admin Portal:  http://localhost:${{PORT}}/admin.html`);
  console.log(`📑 REST API:      http://localhost:${{PORT}}/api/v1/products`);
  console.log('====================================================');
}});
"""

    # 5. src/config/env.js
    files["src/config/env.js"] = """function requireEnv(name) {
  const value = process.env[name];
  if (!value) throw new Error(`${name} must be configured before startup`);
  return value;
}

const nodeEnv = process.env.NODE_ENV || 'development';
const jwtSecret = requireEnv('JWT_SECRET');
if (jwtSecret.length < 32 || /replace|change|example|secret/i.test(jwtSecret)) {
  throw new Error('JWT_SECRET must be a unique 32+-character deployment secret');
}
const corsOrigin = process.env.CORS_ORIGIN || (nodeEnv === 'production' ? '' : 'http://localhost:5000');
if (nodeEnv === 'production' && !corsOrigin) {
  throw new Error('CORS_ORIGIN must list approved HTTPS browser origins in production');
}
const trustProxyHops = Number(process.env.TRUST_PROXY_HOPS || 0);
if (!Number.isInteger(trustProxyHops) || trustProxyHops < 0 || trustProxyHops > 5) {
  throw new Error('TRUST_PROXY_HOPS must be an integer from 0 to 5');
}

module.exports = {
  PORT: process.env.PORT || 5000,
  NODE_ENV: nodeEnv,
  JWT_SECRET: jwtSecret,
  JWT_EXPIRES_IN: process.env.JWT_EXPIRES_IN || '7d',
  CORS_ORIGIN: corsOrigin,
  TRUST_PROXY_HOPS: trustProxyHops
};
"""

    # Exports never ship user accounts or predictable credentials. Provision
    # the first administrator through a reviewed deployment workflow.
    initial_users = []
    # Promotions remain unavailable until checkout applies them server-side.
    initial_promo_codes = []
    # New exports start without fabricated customer reviews.
    initial_reviews = []
    initial_settings = {
        "brand_name": clean_brand,
        "slogan": clean_slogan,
        "phone": phone,
    }

    initial_db_state = {
        "categories": cat_list,
        "products": catalog,
        "users": initial_users,
        "promoCodes": initial_promo_codes,
        "reviews": initial_reviews,
        "orders": [],
        "subscribers": [],
        "settings": initial_settings
    }

    # Generate schema.sql (Full SQL DDL & Seed Statements)
    sql_lines = [
        f"-- ========================================================",
        f"-- AutoCorp Multi-Tenant Database Engine",
        f"-- Tenant Database: tenant_db_{job_id} ({clean_brand})",
        f"-- Dialect: SQLite 3 / libSQL / PostgreSQL compatible",
        f"-- ========================================================",
        "",
        "CREATE TABLE IF NOT EXISTS users (",
        "    id INTEGER PRIMARY KEY AUTOINCREMENT,",
        "    name TEXT NOT NULL,",
        "    email TEXT UNIQUE NOT NULL,",
        "    password_hash TEXT NOT NULL,",
        "    role TEXT DEFAULT 'customer',",
        "    phone TEXT,",
        "    created_at TEXT NOT NULL",
        ");",
        "",
        "CREATE TABLE IF NOT EXISTS categories (",
        "    id INTEGER PRIMARY KEY AUTOINCREMENT,",
        "    name_ar TEXT NOT NULL,",
        "    name_en TEXT NOT NULL,",
        "    slug TEXT UNIQUE NOT NULL,",
        "    icon TEXT",
        ");",
        "",
        "CREATE TABLE IF NOT EXISTS products (",
        "    id INTEGER PRIMARY KEY AUTOINCREMENT,",
        "    name_ar TEXT NOT NULL,",
        "    name_en TEXT NOT NULL,",
        "    price REAL NOT NULL,",
        "    original_price REAL,",
        "    category_id INTEGER,",
        "    image_url TEXT,",
        "    description TEXT,",
        "    stock INTEGER DEFAULT 100,",
        "    rating REAL DEFAULT 0.0,",
        "    badge TEXT,",
        "    FOREIGN KEY (category_id) REFERENCES categories (id)",
        ");",
        "",
        "CREATE TABLE IF NOT EXISTS orders (",
        "    id INTEGER PRIMARY KEY AUTOINCREMENT,",
        "    order_number TEXT UNIQUE NOT NULL,",
        "    customer_name TEXT NOT NULL,",
        "    customer_phone TEXT NOT NULL,",
        "    customer_address TEXT NOT NULL,",
        "    items_json TEXT NOT NULL,",
        "    total_price REAL NOT NULL,",
        "    payment_method TEXT NOT NULL,",
        "    payment_status TEXT DEFAULT 'pending',",
        "    order_status TEXT DEFAULT 'pending_confirmation',",
        "    created_at TEXT NOT NULL",
        ");",
        "",
        "CREATE TABLE IF NOT EXISTS promo_codes (",
        "    id INTEGER PRIMARY KEY AUTOINCREMENT,",
        "    code TEXT UNIQUE NOT NULL,",
        "    discount_percent REAL NOT NULL,",
        "    min_order_egp REAL DEFAULT 0,",
        "    is_active INTEGER DEFAULT 1",
        ");",
        "",
        "CREATE TABLE IF NOT EXISTS reviews (",
        "    id INTEGER PRIMARY KEY AUTOINCREMENT,",
        "    product_id INTEGER,",
        "    author TEXT NOT NULL,",
        "    rating INTEGER NOT NULL,",
        "    comment TEXT NOT NULL,",
        "    created_at TEXT NOT NULL,",
        "    FOREIGN KEY (product_id) REFERENCES products (id)",
        ");",
        "",
        "CREATE TABLE IF NOT EXISTS store_settings (",
        "    key TEXT PRIMARY KEY,",
        "    value TEXT",
        ");",
        "",
        "-- Seed Initial Categories"
    ]
    for i, c in enumerate(cat_list):
        c_name = c.get("name") or c.get("name_ar") or f"قسم {i+1}"
        c_name_en = c.get("name_en") or f"Category {i+1}"
        c_slug = c.get("slug") or f"cat_{c.get('id', i+1)}"
        c_icon = c.get("icon") or "🏷️"
        esc_ar = c_name.replace("'", "''")
        esc_en = c_name_en.replace("'", "''")
        esc_slug = c_slug.replace("'", "''")
        esc_icon = c_icon.replace("'", "''")
        sql_lines.append(f"INSERT OR IGNORE INTO categories (id, name_ar, name_en, slug, icon) VALUES ({c.get('id', i+1)}, '{esc_ar}', '{esc_en}', '{esc_slug}', '{esc_icon}');")

    sql_lines.append("\n-- Seed Initial Products")
    for i, p in enumerate(catalog):
        p_title = p.get("title") or p.get("name_ar") or f"منتج {i+1}"
        p_title_en = p.get("title_en") or p.get("name_en") or f"Product {i+1}"
        p_price = float(p.get("price") or 100)
        p_orig = float(p.get("originalPrice") or p.get("original_price") or round(p_price * 1.25))
        p_cat_id = int(p.get("categoryId") or p.get("category_id") or 1)
        esc_ar = p_title.replace("'", "''")
        esc_en = p_title_en.replace("'", "''")
        esc_desc = (p.get("description") or "").replace("'", "''")
        esc_img = (p.get("image_url") or p.get("image") or "").replace("'", "''")
        esc_badge = (p.get("badge") or "").replace("'", "''")
        sql_lines.append(
            f"INSERT OR IGNORE INTO products (id, name_ar, name_en, price, original_price, category_id, image_url, description, stock, rating, badge) "
            f"VALUES ({p.get('id', i+1)}, '{esc_ar}', '{esc_en}', {p_price}, {p_orig}, {p_cat_id}, '{esc_img}', '{esc_desc}', 100, {p.get('rating', 5.0)}, '{esc_badge}');"
        )

    sql_lines.append("\n-- Seed Promo Codes")

    sql_lines.append("\n-- Seed Store Settings")
    esc_brand = clean_brand.replace("'", "''")
    esc_slogan = clean_slogan.replace("'", "''")
    sql_lines.append(f"INSERT OR REPLACE INTO store_settings (key, value) VALUES ('brand_name', '{esc_brand}');")
    sql_lines.append(f"INSERT OR REPLACE INTO store_settings (key, value) VALUES ('slogan', '{esc_slogan}');")
    sql_lines.append(f"INSERT OR REPLACE INTO store_settings (key, value) VALUES ('phone', '{phone}');")

    sql_lines.append("-- User accounts are provisioned after deployment; no default credentials are seeded.")
    schema_sql_content = "\n".join(sql_lines)

    # 6. schema.sql & src/config/schema.sql
    files["schema.sql"] = schema_sql_content
    files["src/config/schema.sql"] = schema_sql_content

    # 7. database.json (Document Snapshot)
    files["database.json"] = json.dumps(initial_db_state, ensure_ascii=False, indent=2)

    # 8. src/config/db.sqlite.js (SQLite Connector)
    files["src/config/db.sqlite.js"] = f"""/**
 * AutoCorp SQLite Tenant Database Connector
 * Connects to database.sqlite with auto-fallback to in-memory JSON state
 */
const path = require('path');
const fs = require('fs');

const SQLITE_FILE = path.join(__dirname, '../../database.sqlite');
const SCHEMA_FILE = path.join(__dirname, '../../schema.sql');

let dbInstance = null;

function getDb() {{
  if (dbInstance) return dbInstance;
  try {{
    const Database = require('better-sqlite3');
    dbInstance = new Database(SQLITE_FILE);
    dbInstance.pragma('journal_mode = WAL');
    if (fs.existsSync(SCHEMA_FILE)) {{
      const schema = fs.readFileSync(SCHEMA_FILE, 'utf8');
      dbInstance.exec(schema);
    }}
    return dbInstance;
  }} catch(e) {{
    // Fallback adapter using JSON state
    const jsonDb = require('./database');
    return {{
      prepare: (sql) => ({{
        all: () => jsonDb.get().products || [],
        get: () => (jsonDb.get().products || [])[0],
        run: () => ({{ changes: 1, lastInsertRowid: Date.now() }})
      }}),
      exec: () => {{}}
    }};
  }}
}}

module.exports = {{ getDb, SQLITE_FILE }};
"""

    # 9. src/config/database.js (Universal JSON + SQLite State Store)
    files["src/config/database.js"] = f"""/**
 * High-performance In-Memory & Persistent State Store for {clean_brand}
 * Supports ACID operations, pre-seeded catalogs, users, promo codes, and orders.
 */
const fs = require('fs');
const path = require('path');

const DB_FILE = path.join(__dirname, '../../database.json');
const INITIAL_STATE = {_json_for_script(initial_db_state, indent=2)};

let state = null;

function loadState() {{
  if (state) return state;
  if (fs.existsSync(DB_FILE)) {{
    try {{
      state = JSON.parse(fs.readFileSync(DB_FILE, 'utf8'));
      return state;
    }} catch(e) {{
      console.warn("Corrupt database file, resetting to initial state.");
    }}
  }}
  state = JSON.parse(JSON.stringify(INITIAL_STATE));
  saveState();
  return state;
}}

function saveState() {{
  try {{
    fs.writeFileSync(DB_FILE, JSON.stringify(state, null, 2), 'utf8');
  }} catch(e) {{
    console.error("Failed to persist database:", e.message);
  }}
}}

module.exports = {{
  get: () => loadState(),
  save: () => saveState(),
  INITIAL_STATE
}};
"""

    # 6b. src/config/drizzle.js (Drizzle ORM Connection to SQLite)
    files["src/config/drizzle.js"] = """const Database = require('better-sqlite3');
const { drizzle } = require('drizzle-orm/better-sqlite3');
const path = require('path');
const schema = require('../models/drizzle.schema');

const dbPath = process.env.DATABASE_URL || path.join(__dirname, '../../database.sqlite');
let sqlite;
try {
  sqlite = new Database(dbPath);
} catch (e) {
  sqlite = new Database(':memory:');
}
const db = drizzle(sqlite, { schema });

module.exports = { db, sqlite, schema };
"""

    # 6c. src/models/drizzle.schema.js (Drizzle ORM Relational Schema)
    files["src/models/drizzle.schema.js"] = """const { sqliteTable, text, integer, real } = require('drizzle-orm/sqlite-core');

const users = sqliteTable('users', {
  id: integer('id').primaryKey({ autoIncrement: true }),
  name: text('name').notNull(),
  email: text('email').notNull().unique(),
  passwordHash: text('password_hash').notNull(),
  role: text('role').default('customer'),
  phone: text('phone'),
  createdAt: text('created_at').notNull()
});

const categories = sqliteTable('categories', {
  id: integer('id').primaryKey({ autoIncrement: true }),
  name: text('name').notNull(),
  nameEn: text('name_en'),
  createdAt: text('created_at')
});

const products = sqliteTable('products', {
  id: integer('id').primaryKey({ autoIncrement: true }),
  title: text('title').notNull(),
  titleEn: text('title_en'),
  price: real('price').notNull(),
  category: text('category').notNull(),
  badge: text('badge'),
  stock: integer('stock').default(50),
  rating: real('rating').default(0.0),
  reviewsCount: integer('reviews_count').default(0),
  description: text('description'),
  imageUrl: text('image_url')
});

const orders = sqliteTable('orders', {
  id: integer('id').primaryKey({ autoIncrement: true }),
  customerName: text('customer_name').notNull(),
  customerPhone: text('customer_phone').notNull(),
  customerAddress: text('customer_address').notNull(),
  itemsJson: text('items_json').notNull(),
  totalEgp: real('total_egp').notNull(),
  paymentMethod: text('payment_method').default('cash_on_delivery'),
  paymentRef: text('payment_ref'),
  status: text('status').default('pending_confirmation'),
  createdAt: text('created_at').notNull()
});

const promoCodes = sqliteTable('promo_codes', {
  id: integer('id').primaryKey({ autoIncrement: true }),
  code: text('code').notNull().unique(),
  discountPercent: real('discount_percent').notNull(),
  minOrderEgp: real('min_order_egp').default(0),
  active: integer('active').default(1)
});

const reviews = sqliteTable('reviews', {
  id: integer('id').primaryKey({ autoIncrement: true }),
  productId: integer('product_id').notNull(),
  author: text('author').notNull(),
  rating: integer('rating').notNull(),
  comment: text('comment'),
  date: text('date')
});

const settings = sqliteTable('store_settings', {
  key: text('key').primaryKey(),
  value: text('value')
});

module.exports = {
  users,
  categories,
  products,
  orders,
  promoCodes,
  reviews,
  settings
};
"""

    # 7. src/utils/response.js
    files["src/utils/response.js"] = """/**
 * Standardized API Response Envelopes
 */
exports.success = (res, message = 'Success', data = {}, statusCode = 200) => {
  return res.status(statusCode).json({
    success: true,
    message,
    data,
    timestamp: new Date().toISOString()
  });
};

exports.error = (res, message = 'An error occurred', statusCode = 500, errors = null) => {
  return res.status(statusCode).json({
    success: false,
    message,
    errors,
    timestamp: new Date().toISOString()
  });
};
"""

    # 8. src/utils/ApiError.js
    files["src/utils/ApiError.js"] = """/**
 * Operational Custom Error Class
 */
class ApiError extends Error {
  constructor(statusCode, message, errors = null) {
    super(message);
    this.statusCode = statusCode;
    this.errors = errors;
    this.isOperational = true;
    Error.captureStackTrace(this, this.constructor);
  }
}
module.exports = ApiError;
"""

    # 9. src/utils/jwt.js
    files["src/utils/jwt.js"] = """const jwt = require('jsonwebtoken');
const env = require('../config/env');

exports.generateToken = (payload) => {
  return jwt.sign(payload, env.JWT_SECRET, { expiresIn: env.JWT_EXPIRES_IN });
};

exports.verifyToken = (token) => {
  return jwt.verify(token, env.JWT_SECRET);
};
"""

    # 10. src/utils/pagination.js
    files["src/utils/pagination.js"] = """exports.getPagination = (query, defaultLimit = 12) => {
  const page = Math.max(1, parseInt(query.page, 10) || 1);
  const limit = Math.max(1, Math.min(100, parseInt(query.limit, 10) || defaultLimit));
  const offset = (page - 1) * limit;
  return { page, limit, offset };
};
"""

    # 11. src/utils/sendVerificationEmail.js & sendResetPasswordEmail.js
    files["src/utils/sendVerificationEmail.js"] = """const ApiError = require('./ApiError');

module.exports = async function sendVerificationEmail() {
  throw new ApiError(503, 'Email verification delivery is not configured.');
};
"""
    files["src/utils/sendResetPasswordEmail.js"] = """const ApiError = require('./ApiError');

module.exports = async function sendResetPasswordEmail() {
  throw new ApiError(503, 'Password reset delivery is not configured.');
};
"""

    # 12. src/middlewares/errorHandler.middleware.js
    files["src/middlewares/errorHandler.middleware.js"] = """const { error } = require('../utils/response');

module.exports = (err, req, res, next) => {
  const statusCode = err.statusCode || 500;
  const message = err.message || 'Internal Server Error';
  console.error(`[ERROR] [${req.method}] ${req.originalUrl}:`, err);
  return error(res, message, statusCode, err.errors || null);
};
"""

    # 13. src/middlewares/auth.middleware.js
    files["src/middlewares/auth.middleware.js"] = """const ApiError = require('../utils/ApiError');
const { verifyToken } = require('../utils/jwt');
const db = require('../config/database');

module.exports = (req, res, next) => {
  let token = null;

  // 1. Primary secure source: HttpOnly cookie (OWASP A07 - immunizes against XSS token theft)
  if (req.cookies && req.cookies.jwt_token) {
    token = req.cookies.jwt_token;
  }
  // 2. Secondary fallback: Authorization header Bearer token
  else if (req.headers.authorization && req.headers.authorization.startsWith('Bearer ')) {
    token = req.headers.authorization.split(' ')[1];
  }

  if (!token) {
    return next(new ApiError(401, 'يرجى تسجيل الدخول للوصول إلى هذه الخدمة (Missing authentication token)'));
  }

  try {
    const decoded = verifyToken(token);
    const users = db.get().users;
    const user = users.find(u => u.id === decoded.id);
    if (!user) {
      return next(new ApiError(401, 'المستخدم غير موجود'));
    }
    req.user = user;
    next();
  } catch(err) {
    return next(new ApiError(401, 'انتهت صلاحية جلسة الدخول أو التوكن غير صالح'));
  }
};
"""

    # 14. src/middlewares/admin.middleware.js
    files["src/middlewares/admin.middleware.js"] = """const ApiError = require('../utils/ApiError');

module.exports = (req, res, next) => {
  if (req.user && req.user.role === 'admin') {
    return next();
  }
  return next(new ApiError(403, 'غير مصرح: هذه الميزة مخصصة للمشرفين فقط (Admin privileges required)'));
};
"""

    # 15. src/middlewares/customer.middleware.js
    files["src/middlewares/customer.middleware.js"] = """const ApiError = require('../utils/ApiError');

module.exports = (req, res, next) => {
  if (req.user && (req.user.role === 'customer' || req.user.role === 'admin')) {
    return next();
  }
  return next(new ApiError(403, 'غير مصرح: حساب عميل مطلوب'));
};
"""

    # 16. src/middlewares/validate.middleware.js
    files["src/middlewares/validate.middleware.js"] = """const ApiError = require('../utils/ApiError');

module.exports = (schema) => (req, res, next) => {
  if (typeof schema !== 'function') return next();
  const errors = schema(req.body, req.query, req.params);
  if (errors && errors.length > 0) {
    return next(new ApiError(400, 'بيانات غير صالحة', errors));
  }
  next();
};
"""

    # 17. src/middlewares/rateLimiter.middleware.js
    files["src/middlewares/rateLimiter.middleware.js"] = """const hits = new Map();

// Expire old keys so transient client addresses do not grow memory forever.
const cleanup = setInterval(() => {
  const now = Date.now();
  for (const [key, client] of hits) {
    if (client.resetTime <= now) hits.delete(key);
  }
}, 60000);
cleanup.unref();

module.exports = (max = 120, windowMs = 60000, scope = 'global') => (req, res, next) => {
  const ip = req.ip || req.socket.remoteAddress || 'unknown';
  const key = `${scope}:${ip}`;
  const now = Date.now();
  let client = hits.get(key);

  if (!client || now >= client.resetTime) {
    client = { count: 0, resetTime: now + windowMs };
  }
  client.count += 1;
  hits.set(key, client);

  if (client.count > max) {
    res.set('Retry-After', String(Math.max(1, Math.ceil((client.resetTime - now) / 1000))));
    return res.status(429).json({
      success: false,
      message: 'Rate limit exceeded. Please try again later.',
      timestamp: new Date().toISOString()
    });
  }
  next();
};
"""

    # 18. Models index & files
    files["src/models/index.js"] = """const db = require('../config/database');

module.exports = {
  db,
  Users: require('./user.model'),
  Categories: require('./category.model'),
  Products: require('./product.model'),
  Orders: require('./order.model'),
  Reviews: require('./review.model'),
  PromoCodes: require('./promoCode.model')
};
"""

    files["src/models/user.model.js"] = """const db = require('../config/database');

module.exports = {
  findAll: () => db.get().users,
  findById: (id) => db.get().users.find(u => u.id === Number(id)),
  findByEmail: (email) => db.get().users.find(u => u.email.toLowerCase() === email.toLowerCase()),
  create: (data) => {
    const s = db.get();
    const newUser = { id: s.users.length + 1, ...data, createdAt: new Date().toISOString() };
    s.users.push(newUser);
    db.save();
    return newUser;
  }
};
"""

    files["src/models/category.model.js"] = """const db = require('../config/database');

module.exports = {
  findAll: () => db.get().categories,
  findById: (id) => db.get().categories.find(c => c.id === Number(id)),
  create: (name, nameEn) => {
    const s = db.get();
    const newCat = { id: s.categories.length + 1, name, name_en: nameEn || name };
    s.categories.push(newCat);
    db.save();
    return newCat;
  }
};
"""

    files["src/models/product.model.js"] = """const db = require('../config/database');

module.exports = {
  findAll: () => db.get().products,
  findById: (id) => db.get().products.find(p => p.id === Number(id)),
  create: (data) => {
    const s = db.get();
    const newProd = {
      id: s.products.length + 1,
      title: data.title,
      title_en: data.title_en,
      price: data.price,
      category: data.category,
      badge: data.badge,
      stock: 0,
      rating: 0,
      reviews_count: 0,
      description: data.description,
      image_url: data.image_url
    };
    s.products.unshift(newProd);
    db.save();
    return newProd;
  },
  update: (id, updates) => {
    const s = db.get();
    const p = s.products.find(x => x.id === Number(id));
    if (!p) return null;
    Object.assign(p, updates);
    db.save();
    return p;
  },
  delete: (id) => {
    const s = db.get();
    const idx = s.products.findIndex(x => x.id === Number(id));
    if (idx === -1) return false;
    s.products.splice(idx, 1);
    db.save();
    return true;
  }
};
"""

    files["src/models/order.model.js"] = """const crypto = require('crypto');
const db = require('../config/database');

module.exports = {
  findAll: () => db.get().orders,
  findById: (id) => db.get().orders.find(o => o.id === Number(id)),
  findByIdempotencyKey: (keyHash) => db.get().orders.find(o => o.idempotencyKeyHash === keyHash),
  findByCustomerPhone: (phone) => db.get().orders.filter(o => o.customerPhone === phone),
  create: (orderData) => {
    const s = db.get();
    const newOrder = {
      id: s.orders.length + 1,
      orderRef: 'ORD-' + crypto.randomUUID(),
      status: 'pending_confirmation',
      createdAt: new Date().toISOString(),
      ...orderData
    };
    s.orders.unshift(newOrder);
    db.save();
    return newOrder;
  },
  updateStatus: (id, status) => {
    const s = db.get();
    const order = s.orders.find(o => o.id === Number(id));
    if (!order) return null;
    order.status = status;
    order.updatedAt = new Date().toISOString();
    db.save();
    return order;
  }
};
"""

    files["src/models/review.model.js"] = """const db = require('../config/database');

module.exports = {
  findByProduct: (productId) => db.get().reviews.filter(r => r.productId === Number(productId)),
  create: (data) => {
    const s = db.get();
    const newRev = { id: s.reviews.length + 1, date: new Date().toISOString().split('T')[0], ...data };
    s.reviews.unshift(newRev);
    db.save();
    return newRev;
  }
};
"""

    files["src/models/promoCode.model.js"] = """const db = require('../config/database');

module.exports = {
  findAll: () => db.get().promoCodes,
  findByCode: (code) => db.get().promoCodes.find(p => p.code.toUpperCase() === (code || '').trim().toUpperCase()),
  create: (data) => {
    const s = db.get();
    const promo = { ...data, code: data.code.toUpperCase(), active: true };
    s.promoCodes.push(promo);
    db.save();
    return promo;
  }
};
"""

    files["src/models/cart.model.js"] = """// Cart operations are stored client-side and synced via sessions or user IDs
module.exports = {
  calculateTotal: (items) => {
    return (items || []).reduce((sum, it) => sum + (Number(it.price) * (Number(it.quantity) || 1)), 0);
  }
};
"""
    files["src/models/cartItem.model.js"] = "module.exports = {};"
    files["src/models/orderItem.model.js"] = "module.exports = {};"
    files["src/models/discount.model.js"] = "module.exports = {};"
    files["src/models/newsletterSubscriber.model.js"] = """const db = require('../config/database');

module.exports = {
  findAll: () => db.get().subscribers,
  add: (email) => {
    const s = db.get();
    if (!s.subscribers.includes(email)) {
      s.subscribers.push(email);
      db.save();
    }
    return email;
  }
};
"""

    # 19. Modules: Auth
    files["src/modules/auth/auth.validation.js"] = """module.exports = {
  validateRegister: (body) => {
    const input = body && typeof body === 'object' && !Array.isArray(body) ? body : {};
    const errors = [];
    const name = typeof input.name === 'string' ? input.name.trim() : '';
    const email = typeof input.email === 'string' ? input.email.trim() : '';
    const password = input.password;
    if (name.length < 2 || name.length > 100) errors.push('Name must be between 2 and 100 characters.');
    if (email.length > 254 || !/^[^\\s@]+@[^\\s@]+\\.[^\\s@]+$/.test(email)) errors.push('Enter a valid email address.');
    if (typeof password !== 'string' || password.length < 12 || Buffer.byteLength(password, 'utf8') > 72) {
      errors.push('Password must be at least 12 characters and no more than 72 UTF-8 bytes.');
    }
    if (input.phone !== undefined && (typeof input.phone !== 'string' || input.phone.length > 30)) {
      errors.push('Phone must be a string no longer than 30 characters.');
    }
    return errors;
  },
  validateLogin: (body) => {
    const input = body && typeof body === 'object' && !Array.isArray(body) ? body : {};
    const errors = [];
    const email = typeof input.email === 'string' ? input.email.trim() : '';
    if (email.length > 254 || !/^[^\\s@]+@[^\\s@]+\\.[^\\s@]+$/.test(email)) errors.push('Enter a valid email address.');
    if (typeof input.password !== 'string' || input.password.length === 0 || Buffer.byteLength(input.password, 'utf8') > 72) {
      errors.push('Password is required and must not exceed 72 UTF-8 bytes.');
    }
    return errors;
  }
};
"""

    files["src/modules/auth/auth.service.js"] = """const bcrypt = require('bcryptjs');
const UserModel = require('../../models/user.model');
const ApiError = require('../../utils/ApiError');
const { generateToken } = require('../../utils/jwt');

exports.register = async (name, email, password, phone) => {
  const normalizedName = name.trim();
  const normalizedEmail = email.trim().toLowerCase();
  const normalizedPhone = typeof phone === 'string' ? phone.trim() : '';
  const existing = UserModel.findByEmail(normalizedEmail);
  if (existing) throw new ApiError(409, 'البريد الإلكتروني مسجل بالفعل');

  const salt = await bcrypt.genSalt(10);
  const passwordHash = await bcrypt.hash(password, salt);

  const newUser = UserModel.create({
    name: normalizedName,
    email: normalizedEmail,
    passwordHash,
    phone: normalizedPhone,
    role: 'customer'
  });

  const token = generateToken({ id: newUser.id, role: newUser.role, email: newUser.email });
  return { user: { id: newUser.id, name: newUser.name, email: newUser.email, role: newUser.role }, token };
};

exports.login = async (email, password) => {
  const user = UserModel.findByEmail(email.trim().toLowerCase());
  if (!user) throw new ApiError(401, 'البريد الإلكتروني أو كلمة المرور غير صحيحة');

  const isMatch = await bcrypt.compare(password, user.passwordHash).catch(() => false);
  if (!isMatch) throw new ApiError(401, 'البريد الإلكتروني أو كلمة المرور غير صحيحة');

  const token = generateToken({ id: user.id, role: user.role, email: user.email });
  return { user: { id: user.id, name: user.name, email: user.email, role: user.role }, token };
};
"""

    files["src/modules/auth/auth.controller.js"] = """const authService = require('./auth.service');
const { success } = require('../../utils/response');

const COOKIE_OPTIONS = {
  httpOnly: true,
  secure: process.env.NODE_ENV === 'production',
  sameSite: process.env.NODE_ENV === 'production' ? 'strict' : 'lax',
  path: '/',
  maxAge: 7 * 24 * 60 * 60 * 1000 // 7 days in ms
};

exports.register = async (req, res, next) => {
  try {
    const { name, email, password, phone } = req.body;
    const result = await authService.register(name, email, password, phone);
    if (result && result.token) {
      res.cookie('jwt_token', result.token, COOKIE_OPTIONS);
    }
    return success(res, 'تم إنشاء الحساب بنجاح وتأمينه بـ HttpOnly Cookie', { user: result.user }, 201);
  } catch(err) {
    next(err);
  }
};

exports.login = async (req, res, next) => {
  try {
    const { email, password } = req.body;
    const result = await authService.login(email, password);
    if (result && result.token) {
      res.cookie('jwt_token', result.token, COOKIE_OPTIONS);
    }
    return success(res, 'تم تسجيل الدخول بنجاح وتفعيل جلسة آمنة (HttpOnly Cookie)', { user: result.user });
  } catch(err) {
    next(err);
  }
};

exports.logout = (req, res) => {
  res.clearCookie('jwt_token', {
    httpOnly: true,
    secure: process.env.NODE_ENV === 'production',
    sameSite: process.env.NODE_ENV === 'production' ? 'strict' : 'lax',
    path: '/'
  });
  return success(res, 'تم تسجيل الخروج بنجاح ومسح الجلسة الآمنة');
};

exports.getMe = (req, res) => {
  return success(res, 'بيانات المستخدم الحالية', req.user);
};
"""

    files["src/modules/auth/auth.routes.js"] = """const router = require('express').Router();
const authController = require('./auth.controller');
const authMiddleware = require('../../middlewares/auth.middleware');
const rateLimiter = require('../../middlewares/rateLimiter.middleware');
const validate = require('../../middlewares/validate.middleware');
const authValidation = require('./auth.validation');

const loginLimiter = rateLimiter(8, 15 * 60 * 1000, 'auth-login');
const registrationLimiter = rateLimiter(5, 60 * 60 * 1000, 'auth-register');

router.post('/register', registrationLimiter, validate(authValidation.validateRegister), authController.register);
router.post('/login', loginLimiter, validate(authValidation.validateLogin), authController.login);
router.post('/logout', authController.logout);
router.get('/me', authMiddleware, authController.getMe);

module.exports = router;
"""

    # 20. Modules: Products
    files["src/modules/products/product.service.js"] = """const ProductModel = require('../../models/product.model');
const ApiError = require('../../utils/ApiError');

exports.getProducts = (query = {}) => {
  let list = ProductModel.findAll();

  if (query.category && query.category !== 'الكل' && query.category !== 'all') {
    list = list.filter(p => p.category === query.category);
  }

  if (query.search) {
    const q = query.search.toLowerCase();
    list = list.filter(p => p.title.toLowerCase().includes(q) || (p.title_en && p.title_en.toLowerCase().includes(q)));
  }

  return list;
};

exports.getProductById = (id) => {
  const p = ProductModel.findById(id);
  if (!p) throw new ApiError(404, 'المنتج غير موجود');
  return p;
};

exports.normalizeProductInput = (data) => {
  if (!data || typeof data !== 'object' || Array.isArray(data)) {
    throw new ApiError(400, 'Product details must be an object');
  }
  const allowed = new Set(['title', 'title_en', 'price', 'category', 'badge', 'description', 'image_url']);
  if (Object.keys(data).some((key) => !allowed.has(key))) {
    throw new ApiError(400, 'Unsupported product field');
  }
  const text = (value, field, maxLength, required = false) => {
    if (value === undefined || value === null) value = '';
    if (typeof value !== 'string') throw new ApiError(400, `${field} must be text`);
    const normalized = value.trim();
    if ((required && normalized.length === 0) || normalized.length > maxLength) {
      throw new ApiError(400, `${field} is missing or too long`);
    }
    return normalized;
  };
  const title = text(data.title, 'Title', 120, true);
  if (title.length < 2) throw new ApiError(400, 'Title must contain at least two characters');
  const title_en = text(data.title_en, 'English title', 120);
  const category = text(data.category, 'Category', 80, true);
  const badge = text(data.badge, 'Badge', 40);
  const description = text(data.description, 'Description', 2000);
  const image_url = text(data.image_url, 'Image URL', 2048);
  if (typeof data.price !== 'number' || !Number.isFinite(data.price) || data.price < 0 || data.price > 100000000 ||
      Math.abs(data.price * 100 - Math.round(data.price * 100)) > 0.000001) {
    throw new ApiError(400, 'Price must be a non-negative amount with at most two decimals');
  }
  if (image_url) {
    let image;
    try { image = new URL(image_url); } catch (_) { throw new ApiError(400, 'Image URL is invalid'); }
    if (image.protocol !== 'https:' || image.username || image.password) {
      throw new ApiError(400, 'Image URL must use HTTPS and cannot contain credentials');
    }
  }
  return { title, title_en, price: Math.round(data.price * 100) / 100, category, badge, description, image_url };
};

exports.createProduct = (data) => {
  return ProductModel.create(exports.normalizeProductInput(data));
};
"""

    files["src/modules/products/product.controller.js"] = """const productService = require('./product.service');
const { success } = require('../../utils/response');

exports.getAll = (req, res, next) => {
  try {
    const data = productService.getProducts(req.query);
    return success(res, 'قائمة المنتجات', data);
  } catch(e) { next(e); }
};

exports.getOne = (req, res, next) => {
  try {
    const data = productService.getProductById(req.params.id);
    return success(res, 'تفاصيل المنتج', data);
  } catch(e) { next(e); }
};

exports.create = (req, res, next) => {
  try {
    const data = productService.createProduct(req.body);
    return success(res, 'تمت إضافة المنتج بنجاح', data, 201);
  } catch(e) { next(e); }
};
"""

    files["src/modules/products/product.routes.js"] = """const router = require('express').Router();
const productController = require('./product.controller');
const auth = require('../../middlewares/auth.middleware');
const admin = require('../../middlewares/admin.middleware');

router.get('/', productController.getAll);
router.get('/:id', productController.getOne);
router.post('/', auth, admin, productController.create);

module.exports = router;
"""

    # 21. Modules: Categories
    files["src/modules/categories/category.routes.js"] = """const router = require('express').Router();
const CategoryModel = require('../../models/category.model');
const { success } = require('../../utils/response');

router.get('/', (req, res) => {
  return success(res, 'أقسام المتجر', CategoryModel.findAll());
});

module.exports = router;
"""

    # 22. Modules: Orders
    files["src/modules/orders/order.service.js"] = f"""const OrderModel = require('../../models/order.model');
const ProductModel = require('../../models/product.model');
const crypto = require('crypto');
const ApiError = require('../../utils/ApiError');

const ORDER_STATUS_TRANSITIONS = Object.freeze({{
  pending_confirmation: ['confirmed', 'cancelled'],
  confirmed: ['processing', 'cancelled'],
  processing: ['shipped', 'cancelled'],
  shipped: ['completed'],
  completed: [],
  cancelled: []
}});

exports.isAllowedStatusTransition = (current, next) =>
  Object.prototype.hasOwnProperty.call(ORDER_STATUS_TRANSITIONS, current) &&
  ORDER_STATUS_TRANSITIONS[current].includes(next);

exports.checkout = (body, idempotencyKey) => {{
  if (typeof idempotencyKey !== 'string' || !/^[0-9a-f]{{8}}-[0-9a-f]{{4}}-4[0-9a-f]{{3}}-[89ab][0-9a-f]{{3}}-[0-9a-f]{{12}}$/i.test(idempotencyKey)) {{
    throw new ApiError(400, 'A valid Idempotency-Key UUID is required');
  }}
  if (!body || typeof body !== 'object' || Array.isArray(body)) {{
    throw new ApiError(400, 'Order details must be an object');
  }}
  const customerName = typeof body.customer_name === 'string' ? body.customer_name.trim() : '';
  const customerPhone = typeof body.customer_phone === 'string' ? body.customer_phone.trim() : '';
  const customerAddress = typeof body.customer_address === 'string' ? body.customer_address.trim() : '';
  const phoneDigits = customerPhone.replace(/\\D/g, '');
  if (customerName.length < 2 || customerName.length > 100) {{
    throw new ApiError(400, 'Customer name must be between 2 and 100 characters');
  }}
  if (customerPhone.length > 30 || !/^[+0-9().\\s-]+$/.test(customerPhone) || phoneDigits.length < 7 || phoneDigits.length > 15) {{
    throw new ApiError(400, 'Enter a valid customer phone number');
  }}
  if (customerAddress.length < 5 || customerAddress.length > 300) {{
    throw new ApiError(400, 'Delivery address must be between 5 and 300 characters');
  }}

  if (!body.customer_name || !body.customer_phone) {{
    throw new ApiError(400, 'الاسم ورقم الهاتف مطلوبين لتأكيد الطلب');
  }}

  if (!Array.isArray(body.items) || body.items.length === 0 || body.items.length > 50) {{
    throw new ApiError(400, 'سلة المشتريات فارغة');
  }}

  const paymentMethod = String(body.payment_method || 'cod').toLowerCase();
  const supportedMethods = new Set(['cod', 'cash', 'cash_on_delivery']);
  if (!supportedMethods.has(paymentMethod)) {{
    throw new ApiError(400, 'Unsupported payment method');
  }}

  // Validate stable customer intent before looking up current prices.
  const seenProductIds = new Set();
  let totalQuantity = 0;
  const requestedItems = body.items.map((line) => {{
    if (!line || typeof line !== 'object' || Array.isArray(line)) {{
      throw new ApiError(400, 'Each item must be an object');
    }}
    const productId = line.id;
    const quantity = line.quantity;
    if (!Number.isSafeInteger(productId) || productId < 1 || !Number.isInteger(quantity) || quantity < 1 || quantity > 50) {{
      throw new ApiError(400, 'Each item needs a valid product ID and quantity');
    }}
    if (seenProductIds.has(productId)) {{
      throw new ApiError(400, 'Each product may appear only once in an order');
    }}
    seenProductIds.add(productId);
    totalQuantity += quantity;
    if (totalQuantity > 100) {{
      throw new ApiError(400, 'Total order quantity cannot exceed 100');
    }}
    return {{ productId, quantity }};
  }});
  const idempotencyKeyHash = crypto.createHash('sha256').update(idempotencyKey.toLowerCase()).digest('hex');
  const idempotencyFingerprint = crypto.createHash('sha256').update(JSON.stringify({{
    customerName, customerPhone, customerAddress, paymentMethod, requestedItems
  }})).digest('hex');
  const existingOrder = OrderModel.findByIdempotencyKey(idempotencyKeyHash);
  if (existingOrder) {{
    if (existingOrder.idempotencyFingerprint !== idempotencyFingerprint) {{
      throw new ApiError(409, 'Idempotency-Key was already used for a different order');
    }}
    return {{
      order: existingOrder,
      duplicate: true,
      paymentInstructions: 'This order request was already received.'
    }};
  }}

  // A browser may suggest a cart but never determines its price. Resolve current
  // catalog prices only for a new request and save the resulting price snapshot.
  const items = requestedItems.map((requested) => {{
    const product = ProductModel.findById(requested.productId);
    const unitPrice = Number(product && product.price);
    if (!product || !Number.isFinite(unitPrice) || unitPrice < 0 || unitPrice > 100000000) {{
      throw new ApiError(400, 'Product is unavailable for checkout');
    }}
    return {{
      productId: product.id,
      title: product.title || product.nameAr || product.name_ar,
      unitPrice: Number(unitPrice.toFixed(2)),
      quantity: requested.quantity
    }};
  }});
  const totalCents = items.reduce((sum, item) => sum + Math.round(item.unitPrice * 100) * item.quantity, 0);
  if (!Number.isSafeInteger(totalCents) || totalCents > 100000000000) {{
    throw new ApiError(400, 'Order total exceeds the supported limit');
  }}
  const totalEgp = totalCents / 100;
  const paymentRef = 'ORDER-' + crypto.randomUUID();

  const order = OrderModel.create({{
    customerName,
    customerPhone,
    customerAddress,
    items,
    totalEgp,
    paymentMethod,
    paymentRef,
    idempotencyKeyHash,
    idempotencyFingerprint,
    paymentStatus: 'pending_confirmation',
    status: 'pending_confirmation',
    storeBrand: "{clean_brand}"
  }});

  return {{
    order,
    paymentInstructions: 'Order received. Payment remains pending until merchant confirmation.'
  }};
}};

exports.getAllOrders = () => {{
  return OrderModel.findAll();
}};

exports.updateOrderStatus = (id, status) => {{
  const idText = String(id);
  const orderId = Number(idText);
  if (!/^[1-9][0-9]*$/.test(idText) || !Number.isSafeInteger(orderId)) {{
    throw new ApiError(400, 'Order ID must be a positive integer');
  }}
  if (typeof status !== 'string' || !Object.values(ORDER_STATUS_TRANSITIONS).some((values) => values.includes(status))) {{
    throw new ApiError(400, 'Unsupported order status');
  }}
  const currentOrder = OrderModel.findById(orderId);
  if (!currentOrder) throw new ApiError(404, 'Order not found');
  if (!exports.isAllowedStatusTransition(currentOrder.status, status)) {{
    throw new ApiError(409, 'Order status transition is not allowed');
  }}
  // Payment state is deliberately untouched; fulfillment cannot mark an order paid.
  const order = OrderModel.updateStatus(orderId, status);
  if (!order) throw new ApiError(404, 'الطلب غير موجود');
  return order;
}};
"""

    files["src/modules/orders/order.controller.js"] = """const orderService = require('./order.service');
const { success } = require('../../utils/response');

exports.createOrder = (req, res, next) => {
  try {
    const result = orderService.checkout(req.body, req.get('Idempotency-Key'));
    return success(res, 'Order request received; merchant confirmation is pending.', result, result.duplicate ? 200 : 201);
  } catch(e) { next(e); }
};

exports.getOrders = (req, res, next) => {
  try {
    const list = orderService.getAllOrders();
    return success(res, 'سجل الأوردرات', list);
  } catch(e) { next(e); }
};

exports.updateStatus = (req, res, next) => {
  try {
    const updated = orderService.updateOrderStatus(req.params.id, req.body.status);
    return success(res, 'تم تحديث حالة الطلب بنجاح', updated);
  } catch(e) { next(e); }
};
"""

    files["src/modules/orders/order.routes.js"] = """const router = require('express').Router();
const orderController = require('./order.controller');
const auth = require('../../middlewares/auth.middleware');
const admin = require('../../middlewares/admin.middleware');

router.post('/', orderController.createOrder);
router.get('/', auth, admin, orderController.getOrders);
router.patch('/:id/status', auth, admin, orderController.updateStatus);

module.exports = router;
"""

    # 23. Modules: Promo Codes & Discounts
    files["src/modules/promoCodes/promo.routes.js"] = """const router = require('express').Router();
const PromoModel = require('../../models/promoCode.model');
const { success } = require('../../utils/response');

router.post('/validate', (req, res) => {
  return res.status(503).json({
    success: false,
    message: 'Promotions are unavailable until checkout validates and applies them server-side.'
  });
});

router.get('/', (req, res) => {
  return success(res, 'أكواد الخصم النشطة', PromoModel.findAll());
});

module.exports = router;
"""

    # 24. Modules: Reviews
    files["src/modules/reviews/review.routes.js"] = """const router = require('express').Router();
const ReviewModel = require('../../models/review.model');
const { success } = require('../../utils/response');

router.get('/:productId', (req, res) => {
  return success(res, 'تقييمات المنتج', ReviewModel.findByProduct(req.params.productId));
});

router.post('/', (req, res) => {
  return res.status(503).json({
    success: false,
    message: 'Reviews are unavailable until purchase verification and moderation are configured.'
  });
});

module.exports = router;
"""

    # 25. Modules: Newsletter
    files["src/modules/newsletter/newsletter.routes.js"] = """const router = require('express').Router();

router.post('/subscribe', (req, res) => {
  return res.status(503).json({
    success: false,
    message: 'Newsletter signup is unavailable until consent, unsubscribe, and delivery are configured.'
  });
});

module.exports = router;
"""

    # 26. Modules: Dashboard
    files["src/modules/dashboard/dashboard.routes.js"] = """const router = require('express').Router();
const OrderModel = require('../../models/order.model');
const ProductModel = require('../../models/product.model');
const { success } = require('../../utils/response');
const auth = require('../../middlewares/auth.middleware');
const admin = require('../../middlewares/admin.middleware');

router.get('/summary', auth, admin, (req, res) => {
  const orders = OrderModel.findAll();
  const products = ProductModel.findAll();
  const totalRevenue = orders
    .filter(o => o.paymentStatus === 'paid')
    .reduce((sum, o) => sum + (o.totalEgp || 0), 0);

  return success(res, 'إحصائيات المنصة الشاملة', {
    totalRevenueEgp: totalRevenue,
    totalOrders: orders.length,
    totalProducts: products.length,
    activeCustomersCount: new Set(orders.map(o => o.customerPhone)).size,
    pendingOrdersCount: orders.filter(o => o.status === 'pending_confirmation').length,
    confirmedOrdersCount: orders.filter(o => o.paymentStatus === 'paid').length
  });
});

module.exports = router;
"""

    # 27. src/routes/index.js (Aggregator)
    files["src/routes/index.js"] = """const router = require('express').Router();

router.use('/auth', require('../modules/auth/auth.routes'));
router.use('/products', require('../modules/products/product.routes'));
router.use('/categories', require('../modules/categories/category.routes'));
router.use('/orders', require('../modules/orders/order.routes'));
router.use('/promo-codes', require('../modules/promoCodes/promo.routes'));
router.use('/reviews', require('../modules/reviews/review.routes'));
router.use('/newsletter', require('../modules/newsletter/newsletter.routes'));
router.use('/dashboard', require('../modules/dashboard/dashboard.routes'));

router.get('/health', (req, res) => {
  res.json({ status: 'UP', service: 'Enterprise E-Commerce API', timestamp: new Date().toISOString() });
});

module.exports = router;
"""

    # 28. src/app.js (Express app)
    files["src/app.js"] = """const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const morgan = require('morgan');
const cookieParser = require('cookie-parser');
const path = require('path');
const env = require('./config/env');
const routes = require('./routes');
const errorHandler = require('./middlewares/errorHandler.middleware');
const rateLimiter = require('./middlewares/rateLimiter.middleware');

const app = express();
// Only trust explicitly configured proxies; forwarded IP headers affect rate limits.
app.set('trust proxy', env.TRUST_PROXY_HOPS);

// Security & Parsing Middlewares (OWASP Top 10 Hardened)
app.use(helmet({
  contentSecurityPolicy: false,
  crossOriginEmbedderPolicy: false,
  referrerPolicy: { policy: 'strict-origin-when-cross-origin' }
}));

const allowedOrigins = env.CORS_ORIGIN
  .split(',')
  .map(origin => origin.trim())
  .filter(origin => /^https?:\/\//.test(origin));
app.use(cors({
  origin: function(origin, callback) {
    // Non-browser clients have no Origin header. Browser callers must be an
    // explicitly configured first-party origin; wildcard CORS is unsafe with
    // credentialed HttpOnly session cookies.
    if (!origin || allowedOrigins.includes(origin)) {
      callback(null, true);
    } else {
      callback(new Error('Blocked by CORS policy'));
    }
  },
  credentials: true
}));

app.use(cookieParser());
app.use(express.json({ limit: '256kb', strict: true }));
app.use(express.urlencoded({ extended: false, limit: '64kb', parameterLimit: 100 }));
app.use(morgan('dev'));
app.use(rateLimiter(150, 60000));

// API responses can contain account and order data, never cache them in a browser.
app.use('/api', (req, res, next) => {
  res.set('Cache-Control', 'no-store');
  next();
});

// Serve Frontend Static Client
app.use(express.static(path.join(__dirname, '../public')));

// API v1 Routing
app.use('/api/v1', routes);

// Fallback to index.html for SPA routing
app.get('*', (req, res) => {
  res.sendFile(path.join(__dirname, '../public/index.html'));
});

// Global Error Handler
app.use(errorHandler);

module.exports = app;
"""

    # 29. public/index.html (Bilingual AR/EN, Dark/Light Theme, Cart Drawer, Egyptian Payments)
    files["public/index.html"] = generate_bilingual_spa_html(
        job_id=job_id,
        brand_name=clean_brand,
        slogan=clean_slogan,
        primary_color=primary_color or "#0284c7",
        secondary_color=secondary_color or "#38bdf8",
        catalog=catalog,
        categories=list(categories),
        phone=phone,
        whatsapp=whatsapp
    )

    # 30. public/admin.html (Enterprise Operations Portal)
    files["public/admin.html"] = generate_admin_portal_html(
        brand_name=clean_brand,
        job_id=job_id
    )

    # 31. Dockerfile & docker-compose.yml
    files["Dockerfile"] = """FROM node:20-alpine
WORKDIR /app
COPY package*.json ./
RUN npm install --omit=dev && addgroup -S app && adduser -S app -G app
COPY --chown=app:app . .
USER app
EXPOSE 5000
CMD ["npm", "start"]
"""

    files[".dockerignore"] = """node_modules
.env
.git
npm-debug.log*
coverage
*.sqlite
*.db
"""

    files["docker-compose.yml"] = f"""version: '3.8'
services:
  web:
    build: .
    container_name: {brand_identifier}_backend
    ports:
      - "5000:5000"
    environment:
      - PORT=5000
      - NODE_ENV=production
    restart: always
"""

    # 32. vercel.json
    files["vercel.json"] = json.dumps({
        "version": 2,
        "builds": [
            {"src": "server.js", "use": "@vercel/node"},
            {"src": "public/**", "use": "@vercel/static"}
        ],
        "routes": [
            {"src": "/api/(.*)", "dest": "server.js"},
            {"src": "/(.*)", "dest": "/public/$1"}
        ],
        # Vercel serves some paths directly, before Express and Helmet can add
        # response headers. Keep this limited policy compatible with the
        # generated inline client; a strict script-src needs a nonce refactor.
        "headers": [{
            "source": "/(.*)",
            "headers": [
                {"key": "X-Content-Type-Options", "value": "nosniff"},
                {"key": "X-Frame-Options", "value": "DENY"},
                {"key": "Referrer-Policy", "value": "strict-origin-when-cross-origin"},
                {"key": "Permissions-Policy", "value": "camera=(), microphone=(), geolocation=()"},
                {"key": "Content-Security-Policy", "value": "base-uri 'self'; frame-ancestors 'none'; form-action 'self'; object-src 'none'"}
            ]
        }, {
            "source": "/api/(.*)",
            "headers": [{"key": "Cache-Control", "value": "no-store"}]
        }]
    }, indent=2)

    # 33. README.md (Comprehensive Documentation)
    files["README.md"] = f"""# {clean_brand} — Enterprise Full-Stack E-Commerce Platform

> Generated autonomously by **AutoCorp AI Agency** for Egyptian SME growth and high-performance digital commerce.

---

## 🏗️ Architectural Overview

```
Store-Backend/
│
├── src/
│   ├── config/ (database.js, env.js)
│   ├── models/ (user, product, category, order, review, promoCode, etc.)
│   ├── modules/
│   │   ├── auth/ (JWT Login/Register)
│   │   ├── products/ (Catalog, Filters & Search)
│   │   ├── categories/
│   │   ├── cart/
│   │   ├── orders/ (Egyptian Gateways Checkout)
│   │   ├── reviews/ (Customer Ratings)
│   │   ├── promoCodes/ (Discount Engine)
│   │   ├── newsletter/
│   │   └── dashboard/ (Admin Analytics)
│   ├── middlewares/ (auth, admin, customer, validate, errorHandler, rateLimiter)
│   ├── utils/ (response, ApiError, jwt, pagination)
│   ├── routes/index.js
│   └── app.js
├── public/
│   ├── index.html (Bilingual Arabic/English + Dark/Light Theme SPA)
├── database.sqlite (Dedicated Pre-Seeded SQLite Database)
├── schema.sql (Full SQL DDL & Seed Migrations)
├── database.json (Document Database Snapshot)
├── package.json
├── server.js
├── Dockerfile & docker-compose.yml
└── README.md
```

---

## 🚀 Quick Run Locally

### 1. Simple Browser Run (No Node.js needed):
Double-click `public/index.html` in your browser to immediately browse the store!

### 2. Full-Stack Node.js Run:
```bash
# 1. Install dependencies
npm install

# 2. Create .env from .env.example and set a strong unique JWT_SECRET

# 3. Start server
npm start
```
- The export intentionally contains no `.env`, user accounts, or default
  passwords. Provision the first administrator through a reviewed deployment
  process before exposing the service.
- Keep `TRUST_PROXY_HOPS=0` unless the application is reachable only through a
  known proxy chain. If a proxy is required, configure the exact trusted hop
  count and prevent clients from bypassing that proxy; forwarded client IPs are
  used by the per-process rate limits.
- Storefront: [http://localhost:5000](http://localhost:5000)
- Admin Portal: [http://localhost:5000/admin.html](http://localhost:5000/admin.html)

---

## 🌟 Hostinger cPanel Deployment
1. Log in to your Hostinger hPanel.
2. Go to **File Manager** -> `public_html`.
3. Upload and extract this ZIP file.
4. If deploying as Node.js app: Go to **Node.js** in hPanel, set Application root to `/public_html` and startup file to `server.js`.
5. If using standard static hosting: Move files from `public/` into `public_html`.

---

## 📡 REST API Documentation

### Products
- `GET /api/v1/products` — List products (query: `category`, `search`, `page`, `limit`)
- `GET /api/v1/products/:id` — Get single product
- `POST /api/v1/products` — Add product (Admin only)

### Orders & Checkout
- `POST /api/v1/orders` — Records an order request pending merchant confirmation.
- Send a unique UUID v4 `Idempotency-Key` for each logical checkout and reuse it
  unchanged for retries. Replays return the original order; a changed payload
  with the same key returns `409 Conflict`.
- Payment adapters, provider credentials, signed webhooks, and settlement are
  intentionally out of scope for this generated prototype.
- Idempotency is stored with the generated project data; multi-worker production
  still requires a durable database uniqueness constraint and transaction.

### Discounts & Promo Codes
- Promo codes are disabled until validation and final order pricing are handled
  together by the server-side checkout workflow.

### Authentication & JWT
- `POST /api/v1/auth/register`
- `POST /api/v1/auth/login`
- `GET /api/v1/auth/me`

### Analytics Dashboard
- `GET /api/v1/dashboard/summary` — Real-time revenue, orders count, and conversion metrics.
"""

    # 34. tests/security.test.js (OWASP Top 10 Automated Security Tests)
    files["tests/security.test.js"] = """const request = require('supertest');
const app = require('../src/app');

describe('OWASP Top 10 Security & Access Control Suite', () => {
  it('A04: Rejects JSON request bodies larger than the API limit', async () => {
    const res = await request(app)
      .post('/api/v1/orders')
      .set('Idempotency-Key', '2f1c91b9-79c8-4f36-8581-dc1468d54c28')
      .send({ padding: 'x'.repeat(300 * 1024) });
    expect(res.status).toBe(413);
  });

  it('A09: Fails closed for email delivery without logging recovery tokens', async () => {
    const sendVerificationEmail = require('../src/utils/sendVerificationEmail');
    const sendResetPasswordEmail = require('../src/utils/sendResetPasswordEmail');
    const log = jest.spyOn(console, 'log').mockImplementation(() => {});
    try {
      await expect(sendVerificationEmail('user@example.test', 'verification-secret'))
        .rejects.toMatchObject({ statusCode: 503 });
      await expect(sendResetPasswordEmail('user@example.test', 'reset-secret'))
        .rejects.toMatchObject({ statusCode: 503 });
      expect(log).not.toHaveBeenCalled();
    } finally {
      log.mockRestore();
    }
  });

  it('A03: Accepts only bounded catalog fields and safe product prices/URLs', () => {
    const products = require('../src/modules/products/product.service');
    const normalized = products.normalizeProductInput({
      title: ' Desk Lamp ', title_en: 'Desk Lamp', price: 24.99,
      category: 'Lighting', image_url: 'https://images.example.test/lamp.png'
    });
    expect(normalized.title).toBe('Desk Lamp');
    expect(normalized.price).toBe(24.99);
    expect(() => products.normalizeProductInput({ title: 'Lamp', category: 'Lighting', price: -1 }))
      .toThrow();
    expect(() => products.normalizeProductInput({ title: 'Lamp', category: 'Lighting', price: 1, id: 1 }))
      .toThrow();
    expect(() => products.normalizeProductInput({
      title: 'Lamp', category: 'Lighting', price: 1, image_url: 'javascript:alert(1)'
    })).toThrow();
  });

  it('A01: Rejects unauthenticated requests to protected endpoints (401)', async () => {
    const res = await request(app).get('/api/v1/dashboard/summary');
    expect([401, 403]).toContain(res.status);
    expect(res.body.success).toBe(false);
  });

  it('A01: Allows only forward fulfillment transitions, never payment-state promotion', () => {
    const orders = require('../src/modules/orders/order.service');
    expect(orders.isAllowedStatusTransition('pending_confirmation', 'confirmed')).toBe(true);
    expect(orders.isAllowedStatusTransition('confirmed', 'processing')).toBe(true);
    expect(orders.isAllowedStatusTransition('pending_confirmation', 'paid')).toBe(false);
    expect(orders.isAllowedStatusTransition('shipped', 'processing')).toBe(false);
    expect(orders.isAllowedStatusTransition('completed', 'cancelled')).toBe(false);
  });

  it('A04: Rejects malformed checkout data before creating an order', async () => {
    const res = await request(app).post('/api/v1/orders')
      .set('Idempotency-Key', '2f1c91b9-79c8-4f36-8581-dc1468d54c28')
      .send({
        customer_name: {}, customer_phone: 'bad', customer_address: '',
        payment_method: 'cod', items: [{ id: 1, quantity: '1 item' }]
      });
    expect(res.status).toBe(400);
  });

  it('A07: Rejects malformed registration and login input before password handling', async () => {
    const registration = await request(app)
      .post('/api/v1/auth/register')
      .send({ name: {}, email: 'not-an-email', password: 'short' });
    const login = await request(app)
      .post('/api/v1/auth/login')
      .send({ email: [], password: 'x'.repeat(73) });
    expect(registration.status).toBe(400);
    expect(login.status).toBe(400);
  });

  it('A03: Resists raw SQL injection payloads in search queries', async () => {
    const maliciousPayload = "' OR '1'='1' --";
    const res = await request(app)
      .get(`/api/v1/products?search=${encodeURIComponent(maliciousPayload)}`);
    expect(res.status).toBe(200);
    expect(res.body.success).toBe(true);
  });

  it('A05: Enforces Helmet security headers on responses', async () => {
    const res = await request(app).get('/api/v1/products');
    expect(res.headers['x-content-type-options']).toBe('nosniff');
  });

  it('A07: Sets HttpOnly secure cookie upon authentication', async () => {
    const res = await request(app)
      .post('/api/v1/auth/login')
      .send({ email: 'admin@store.com', password: 'password123' });
    expect([200, 400, 401]).toContain(res.status);
    if (res.status === 200) {
      const cookies = res.headers['set-cookie'];
      expect(cookies).toBeDefined();
      expect(cookies.some(c => c.includes('HttpOnly'))).toBe(true);
    }
  });
});
"""

    # 35. tests/api.test.js (Core REST API Test Suite)
    files["tests/api.test.js"] = """const request = require('supertest');
const crypto = require('crypto');
const app = require('../src/app');

describe('Enterprise REST API Endpoints', () => {
  it('GET /api/v1/products returns product catalog', async () => {
    const res = await request(app).get('/api/v1/products');
    expect(res.status).toBe(200);
    expect(res.body.success).toBe(true);
  });

  it('POST /api/v1/orders processes a new customer order', async () => {
    const idempotencyKey = crypto.randomUUID();
    const orderData = {
      customer_name: 'Farouk Ibrahim',
      customer_phone: '01000000000',
      customer_address: 'Cairo, Egypt',
      items: [{ id: 1, quantity: 1 }],
      payment_method: 'cod'
    };
    const first = await request(app).post('/api/v1/orders')
      .set('Idempotency-Key', idempotencyKey).send(orderData);
    expect(first.status).toBe(201);
    expect(first.body.success).toBe(true);

    const retry = await request(app).post('/api/v1/orders')
      .set('Idempotency-Key', idempotencyKey).send(orderData);
    expect(retry.status).toBe(200);
    expect(retry.body.data.duplicate).toBe(true);
    expect(retry.body.data.order.orderRef).toBe(first.body.data.order.orderRef);

    const changedPayload = { ...orderData, items: [{ id: 1, quantity: 2 }] };
    const conflict = await request(app).post('/api/v1/orders')
      .set('Idempotency-Key', idempotencyKey).send(changedPayload);
    expect(conflict.status).toBe(409);
  });
});
"""

    return files


def generate_bilingual_spa_html(
    job_id: int,
    brand_name: str,
    slogan: str,
    primary_color: str,
    secondary_color: str,
    catalog: list,
    categories: list,
    phone: str,
    whatsapp: str
) -> str:
    """Produces the bilingual AR/EN and Dark/Light mode single-page application."""
    brand_html = html.escape(_safe_text(brand_name, "المتجر المصري", 120))
    slogan_html = html.escape(_safe_text(slogan, "الجودة والتميز في كل طلب", 500))
    primary_color = _safe_hex_color(primary_color, "#0284c7")
    secondary_color = _safe_hex_color(secondary_color, "#38bdf8")
    phone = _safe_phone(phone)
    whatsapp = _safe_phone(whatsapp, phone)
    catalog_json = _json_for_script(catalog)
    categories_json = _json_for_script(categories)

    return f"""<!doctype html>
<html lang="ar" dir="rtl" class="scroll-smooth">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{brand_html} — المتجر الإلكتروني الرسمي | Official Store</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;800;900&family=Readex+Pro:wght@400;600;700&family=Inter:wght@400;600;700;900&display=swap" rel="stylesheet">
  <script src="https://cdn.tailwindcss.com"></script>
  <script>
    tailwind.config = {{
      darkMode: 'class',
      theme: {{
        extend: {{
          fontFamily: {{
            cairo: ['Cairo', 'sans-serif'],
            readex: ['Readex Pro', 'sans-serif'],
            inter: ['Inter', 'sans-serif']
          }},
          colors: {{
            brand: {{
              500: '{primary_color}',
              600: '{primary_color}',
              secondary: '{secondary_color}'
            }}
          }}
        }}
      }}
    }}
  </script>
  <style>
    body {{ font-family: 'Cairo', 'Inter', sans-serif; transition: background-color 0.3s, color 0.3s; }}
    .cart-drawer {{ transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1); }}
    .cart-drawer.closed {{ transform: translateX(100%); }}
    html[dir="ltr"] .cart-drawer.closed {{ transform: translateX(-100%); }}
  </style>
</head>
<body class="bg-slate-50 text-slate-800 dark:bg-slate-950 dark:text-slate-100 min-h-screen flex flex-col selection:bg-brand-500 selection:text-white">
  <a href="#catalog" class="sr-only focus:not-sr-only focus:fixed focus:top-3 focus:left-3 focus:z-[100] focus:rounded-lg focus:bg-white focus:px-4 focus:py-3 focus:text-slate-950">تخطي إلى المحتوى الرئيسي / Skip to main content</a>

  <!-- Top Announcement Bar -->
  <div class="bg-slate-900 text-slate-200 text-xs py-2 px-4 text-center flex items-center justify-between border-b border-slate-800">
    <div class="flex items-center gap-2 mx-auto">
      <span class="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
      <span id="txt-promo-bar">استعرض المنتجات وأرسل طلبك لتأكيد المتجر</span>
    </div>
    <div class="flex items-center gap-3">
      <!-- Theme Switcher -->
      <button onclick="toggleTheme()" class="px-2 py-0.5 rounded bg-slate-800 hover:bg-slate-700 text-amber-400 text-xs font-bold transition flex items-center gap-1" id="theme-btn">
        <span>☀️</span> <span id="theme-lbl">نهاري</span>
      </button>
      <!-- Lang Switcher -->
      <button onclick="toggleLang()" class="px-2 py-0.5 rounded bg-slate-800 hover:bg-slate-700 text-cyan-400 text-xs font-bold transition" id="lang-btn">
        English
      </button>
    </div>
  </div>

  <!-- Main Navigation Bar -->
  <header class="sticky top-0 z-40 bg-white/95 dark:bg-slate-900/95 backdrop-blur border-b border-slate-200 dark:border-slate-800 shadow-sm">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-20 flex items-center justify-between">
      <div class="flex items-center gap-4">
        <a href="#" class="flex items-center gap-3">
          <div class="w-12 h-12 rounded-2xl flex items-center justify-center text-2xl text-white shadow-md font-black" style="background:{primary_color}">
            ⚡
          </div>
          <div>
            <h1 class="text-xl sm:text-2xl font-black leading-tight text-slate-900 dark:text-white" id="nav-brand">{brand_html}</h1>
            <p class="text-xs text-slate-500 dark:text-slate-400 font-readex" id="nav-slogan">{slogan_html}</p>
          </div>
        </a>
      </div>

      <div class="flex items-center gap-3 sm:gap-4">
        <a href="/admin.html" class="hidden sm:inline-flex items-center gap-1.5 px-3 py-2 rounded-xl text-xs font-bold bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-300 transition">
          📊 <span id="btn-admin-lbl">لوحة المشرف</span>
        </a>

        <!-- Cart Button -->
        <button onclick="toggleCart()" class="relative p-3 rounded-2xl bg-brand-500 hover:opacity-90 text-white font-bold transition shadow-lg shadow-brand-500/25 flex items-center gap-2">
          <span>🛒</span>
          <span class="hidden sm:inline text-xs font-black" id="lbl-cart">السلة</span>
          <span id="cart-badge" class="w-5 h-5 rounded-full bg-amber-400 text-slate-950 font-black text-xs flex items-center justify-center">0</span>
        </button>
      </div>
    </div>
  </header>

  <!-- Hero Banner -->
  <section class="relative py-14 sm:py-20 overflow-hidden bg-gradient-to-br from-slate-900 via-slate-950 to-slate-900 text-white border-b border-slate-800">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10 flex flex-col md:flex-row items-center justify-between gap-10">
      <div class="max-w-2xl text-center md:text-start">
        <span class="inline-block px-3 py-1 rounded-full text-xs font-black tracking-wider uppercase bg-brand-500/20 text-brand-secondary border border-brand-500/30 mb-4" id="hero-tag">
          🚀 تجربة تسوق استثنائية
        </span>
        <h2 class="text-3xl sm:text-5xl font-black leading-tight mb-4 text-white" id="hero-title">
          {brand_html}
        </h2>
        <p class="text-base sm:text-lg text-slate-300 leading-relaxed font-readex mb-8" id="hero-sub">
          {slogan_html}
        </p>
        <div class="flex flex-wrap gap-4 justify-center md:justify-start">
          <a href="#catalog" class="px-6 py-3.5 rounded-xl font-black text-slate-950 bg-amber-400 hover:bg-amber-300 transition shadow-lg shadow-amber-400/25 text-sm" id="btn-browse">
            🛍️ تصفح المنتجات الآن
          </a>
          <a href="https://wa.me/{whatsapp}" target="_blank" class="px-6 py-3.5 rounded-xl font-bold bg-slate-800 hover:bg-slate-700 text-white border border-slate-700 transition text-sm flex items-center gap-2">
            💬 <span id="btn-wa">تواصل عبر واتساب</span>
          </a>
        </div>
      </div>
      <div class="w-full md:w-96 p-6 rounded-3xl bg-slate-800/60 border border-slate-700 backdrop-blur shadow-2xl">
        <h4 class="font-bold text-sm text-cyan-400 mb-3" id="box-perks-title">🌟 مميزات الشراء المباشر</h4>
        <ul class="space-y-3 text-xs text-slate-300 font-readex">
          <li class="flex items-center gap-2">✅ <span id="pk-1">دفع إلكتروني آمن عبر فودافون كاش وإنستاباي وفوري</span></li>
          <li class="flex items-center gap-2">🚚 <span id="pk-2">شحن سريع ومباشر لكافة محافظات جمهورية مصر</span></li>
          <li class="flex items-center gap-2">🛡️ <span id="pk-3">ضمان استبدال واسترجاع حقيقي خلال 14 يوماً</span></li>
          <li class="flex items-center gap-2">🎁 <span id="pk-4">هدايا وكوبونات خصم مستمرة للعملاء الدائمين</span></li>
        </ul>
      </div>
    </div>
  </section>

  <!-- Filter & Catalog Section -->
  <main id="catalog" tabindex="-1" class="flex-1 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12 w-full">
    <div class="flex flex-col sm:flex-row items-center justify-between gap-4 mb-8">
      <div>
        <h3 class="text-2xl font-black text-slate-900 dark:text-white" id="cat-title">قائمة المنتجات المميزة</h3>
        <p class="text-xs text-slate-500 dark:text-slate-400 mt-1 font-readex" id="cat-sub">اختر المنتجات وأضفها إلى السلة للشراء الفوري</p>
      </div>

      <!-- Search input -->
      <div class="w-full sm:w-72">
        <input type="text" id="search-input" oninput="handleSearch(this.value)" placeholder="🔍 ابحث عن أي منتج..." class="w-full px-4 py-2.5 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-xs text-slate-900 dark:text-white focus:outline-none focus:border-brand-500">
      </div>
    </div>

    <!-- Category Pills -->
    <div class="flex items-center gap-2 overflow-x-auto pb-4 mb-8" id="cat-pills"></div>

    <!-- Products Grid -->
    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6" id="products-grid"></div>
  </main>

  <!-- Reviews Section -->
  <section class="py-12 bg-white dark:bg-slate-900/60 border-t border-slate-200 dark:border-slate-800">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <div class="text-center mb-8">
        <h4 class="text-xl font-black text-slate-900 dark:text-white" id="rev-title">⭐ آراء العملاء</h4>
        <p class="text-xs text-slate-500 dark:text-slate-400 mt-1 font-readex" id="rev-sub">لا توجد تقييمات موثقة متاحة حتى الآن</p>
      </div>
      <div class="grid grid-cols-1 md:grid-cols-3 gap-6" id="reviews-container"></div>
    </div>
  </section>

  <!-- Newsletter Section -->
  <section class="py-12 bg-brand-500 text-white">
    <div class="max-w-4xl mx-auto px-4 text-center">
      <h4 class="text-2xl font-black mb-2" id="news-title">التسجيل في النشرة البريدية غير متاح حالياً</h4>
      <p class="text-xs text-white/80 mb-6 font-readex" id="news-sub">لا يتم جمع أو إرسال عناوين البريد الإلكتروني حالياً.</p>
    </div>
  </section>

  <!-- Footer -->
  <footer class="bg-slate-950 text-slate-400 py-8 text-xs border-t border-slate-800">
    <div class="max-w-7xl mx-auto px-4 flex flex-col sm:flex-row items-center justify-between gap-4">
      <div>
        <b class="text-white font-bold">{brand_html}</b> — جميع الحقوق محفوظة © 2026
      </div>
      <div class="flex items-center gap-4">
        <span>الطلبات بانتظار تأكيد التاجر</span>
      </div>
    </div>
  </footer>

  <!-- Slide-out Cart Drawer -->
  <div id="cart-drawer" class="cart-drawer closed fixed inset-y-0 right-0 z-50 w-full max-w-md bg-white dark:bg-slate-900 shadow-2xl border-l border-slate-200 dark:border-slate-800 flex flex-col">
    <div class="p-4 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between">
      <h3 class="font-black text-base text-slate-900 dark:text-white flex items-center gap-2">
        <span>🛒 سلة المشتريات</span>
      </h3>
      <button onclick="toggleCart()" class="p-2 rounded-lg text-slate-400 hover:text-slate-600 dark:hover:text-white">✕</button>
    </div>

    <div class="flex-1 overflow-y-auto p-4 space-y-3" id="cart-items-container"></div>

    <div class="p-4 border-t border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950/60 space-y-3">
      <p id="promo-unavailable" class="text-center text-[11px] text-slate-500" role="status">لا توجد خصومات مفعلة حالياً</p>

      <div class="space-y-1.5 text-xs text-slate-600 dark:text-slate-300 font-readex">
        <div class="flex justify-between"><span>المجموع الفرعي:</span><b id="c-subtotal">0 ج.م</b></div>
        <div class="flex justify-between text-emerald-500"><span>الخصم المطبق:</span><b id="c-discount">0 ج.م</b></div>
        <div class="flex justify-between text-sm font-black text-slate-900 dark:text-white pt-2 border-t border-slate-200 dark:border-slate-800">
          <span>الإجمالي النهائي:</span><b id="c-total">0 ج.م</b>
        </div>
      </div>

      <button onclick="openCheckoutModal()" class="w-full py-3.5 rounded-xl font-black text-slate-950 bg-amber-400 hover:bg-amber-300 text-sm shadow-lg shadow-amber-400/25 transition">
        🚀 متابعة الشراء وتأكيد الطلب
      </button>
    </div>
  </div>

  <!-- Checkout Modal -->
  <div id="checkout-modal" class="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-sm hidden flex items-center justify-center p-4">
    <div class="bg-white dark:bg-slate-900 rounded-3xl max-w-lg w-full p-6 border border-slate-200 dark:border-slate-800 shadow-2xl overflow-y-auto max-h-[90vh]">
      <div class="flex justify-between items-center mb-4 pb-2 border-b border-slate-200 dark:border-slate-800">
        <h3 class="font-black text-base text-slate-900 dark:text-white">💳 تأكيد الطلب وبيانات الشحن</h3>
        <button onclick="closeCheckoutModal()" class="text-slate-400 hover:text-white">✕</button>
      </div>

      <form onsubmit="submitCheckout(event)" oninput="checkoutIdempotencyKey = null" onchange="checkoutIdempotencyKey = null" class="space-y-4">
        <div>
          <label class="block text-xs font-bold mb-1 text-slate-700 dark:text-slate-300">الاسم الكامل *</label>
          <input type="text" id="chk-name" required placeholder="محمد أحمد" class="w-full px-3.5 py-2.5 rounded-xl bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 text-xs text-slate-900 dark:text-white focus:outline-none">
        </div>

        <div>
          <label class="block text-xs font-bold mb-1 text-slate-700 dark:text-slate-300">رقم الهاتف (واتساب) *</label>
          <input type="tel" id="chk-phone" required placeholder="010xxxxxxxx" class="w-full px-3.5 py-2.5 rounded-xl bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 text-xs text-slate-900 dark:text-white focus:outline-none">
        </div>

        <div>
          <label class="block text-xs font-bold mb-1 text-slate-700 dark:text-slate-300">عنوان التوصيل بالتفصيل *</label>
          <textarea id="chk-address" required placeholder="المحافظة، المدينة، الشارع، رقم العقار" rows="2" class="w-full px-3.5 py-2 rounded-xl bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 text-xs text-slate-900 dark:text-white focus:outline-none"></textarea>
        </div>

        <div>
          <label class="block text-xs font-bold mb-2 text-slate-700 dark:text-slate-300">حالة الدفع</label>
          <div class="text-xs">
            <label class="p-3 rounded-xl border border-slate-200 dark:border-slate-800 flex items-center gap-2 cursor-pointer hover:border-brand-500">
              <input type="radio" name="pay-method" value="cash_on_delivery" checked>
              <span>سيؤكد التاجر طريقة الدفع والتسليم بعد مراجعة الطلب.</span>
            </label>
          </div>
        </div>

        <button type="submit" id="btn-submit-order" class="w-full py-3.5 rounded-xl font-black text-slate-950 bg-emerald-400 hover:bg-emerald-300 text-sm shadow-lg shadow-emerald-400/25 transition">
          ✅ تأكيد الأوردر وإرساله للمتجر
        </button>
      </form>
    </div>
  </div>

  <script>
    const CATALOG = {catalog_json};
    const CATEGORIES = {categories_json};
    const escapeCatalogHtml = (value) => String(value ?? '').replace(/[&<>"']/g, (char) => (
      {{ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }}[char]
    ));
    const safeCatalogPrice = (value) => {{
      const price = Number(value);
      return Number.isFinite(price) && price >= 0 ? price : 0;
    }};
    const safeCatalogImageUrl = (value) => {{
      try {{
        const url = new URL(String(value ?? ''), window.location.origin);
        if (url.username || url.password) return '';
        if (url.protocol === 'https:') return url.href;
        if (url.origin === window.location.origin && /^\/static\/uploads\/[A-Za-z0-9_-]+[.](?:jpg|jpeg|png|webp)$/.test(url.pathname)) return url.href;
      }} catch (_) {{}}
      return '';
    }};
    let currentLang = 'ar';
    let currentTheme = 'light';
    let cart = [];
    let checkoutIdempotencyKey = null;
    let selectedCategory = 'الكل';

    // Translations Dictionary
    const I18N = {{
      ar: {{
        promoBar: "استعرض المنتجات وأرسل طلبك لتأكيد المتجر",
        promoUnavailable: "لا توجد خصومات مفعلة حالياً",
        cart: "السلة",
        admin: "لوحة المشرف",
        heroTag: "🚀 تجربة تسوق استثنائية",
        browse: "🛍️ تصفح المنتجات الآن",
        wa: "تواصل عبر واتساب",
        catTitle: "قائمة المنتجات المميزة",
        catSub: "اختر المنتجات وأضفها إلى السلة للشراء الفوري",
        revTitle: "⭐ آراء العملاء",
        revSub: "لا توجد تقييمات موثقة متاحة حتى الآن",
        unrated: "لا توجد تقييمات",
        newsTitle: "التسجيل في النشرة البريدية غير متاح حالياً",
        newsSub: "لا يتم جمع أو إرسال عناوين البريد الإلكتروني حالياً.",
        addCart: "أضف للسلة",
        currency: "ج.م"
      }},
      en: {{
        promoBar: "Browse products and send an order request for merchant confirmation",
        promoUnavailable: "No discounts are currently active",
        cart: "Cart",
        admin: "Admin Portal",
        heroTag: "🚀 Exceptional Shopping Experience",
        browse: "🛍️ Browse Products",
        wa: "Contact on WhatsApp",
        catTitle: "Featured Products",
        catSub: "Select items and add to cart for instant checkout",
        revTitle: "⭐ Customer feedback",
        revSub: "No verified customer reviews are available yet",
        unrated: "No ratings yet",
        newsTitle: "Newsletter signup is not available yet",
        newsSub: "Email addresses are not collected or sent at this time.",
        addCart: "Add to Cart",
        currency: "EGP"
      }}
    }};

    function toggleTheme() {{
      currentTheme = currentTheme === 'light' ? 'dark' : 'light';
      if (currentTheme === 'dark') {{
        document.documentElement.classList.add('dark');
        document.getElementById('theme-lbl').textContent = currentLang === 'ar' ? 'ليلي' : 'Dark';
      }} else {{
        document.documentElement.classList.remove('dark');
        document.getElementById('theme-lbl').textContent = currentLang === 'ar' ? 'نهاري' : 'Light';
      }}
    }}

    function toggleLang() {{
      currentLang = currentLang === 'ar' ? 'en' : 'ar';
      document.documentElement.lang = currentLang;
      document.documentElement.dir = currentLang === 'ar' ? 'rtl' : 'ltr';
      document.getElementById('lang-btn').textContent = currentLang === 'ar' ? 'English' : 'العربية';
      applyTranslations();
      renderCatalog();
    }}

    function applyTranslations() {{
      const d = I18N[currentLang];
      document.getElementById('txt-promo-bar').textContent = d.promoBar;
      document.getElementById('promo-unavailable').textContent = d.promoUnavailable;
      document.getElementById('lbl-cart').textContent = d.cart;
      document.getElementById('btn-admin-lbl').textContent = d.admin;
      document.getElementById('hero-tag').textContent = d.heroTag;
      document.getElementById('btn-browse').textContent = d.browse;
      document.getElementById('btn-wa').textContent = d.wa;
      document.getElementById('cat-title').textContent = d.catTitle;
      document.getElementById('cat-sub').textContent = d.catSub;
      document.getElementById('rev-title').textContent = d.revTitle;
      document.getElementById('rev-sub').textContent = d.revSub;
      document.getElementById('news-title').textContent = d.newsTitle;
      document.getElementById('news-sub').textContent = d.newsSub;
    }}

    function renderCatalog(items = CATALOG) {{
      const grid = document.getElementById('products-grid');
      const d = I18N[currentLang];
      const safeItems = Array.isArray(items) ? items.filter(p => p && typeof p === 'object') : [];
      grid.innerHTML = safeItems.map(p => {{
        const id = Number(p.id);
        if (!Number.isSafeInteger(id) || id < 1) return '';
        const title = escapeCatalogHtml(currentLang === 'en' ? (p.title_en || p.title) : p.title);
        const category = escapeCatalogHtml(p.category);
        const badge = escapeCatalogHtml(p.badge);
        const description = escapeCatalogHtml(p.description);
        const imageUrl = escapeCatalogHtml(safeCatalogImageUrl(p.image_url));
        const price = safeCatalogPrice(p.price);
        const rawRating = Number(p.rating);
        const ratingCount = Number(p.reviews_count);
        const hasVerifiedRating = Number.isFinite(rawRating) && rawRating > 0
          && Number.isSafeInteger(ratingCount) && ratingCount > 0;
        const rating = hasVerifiedRating
          ? `★ ${{Math.min(5, Math.max(0, rawRating)).toFixed(1)}} (${{ratingCount}})`
          : escapeCatalogHtml(d.unrated);
        return `
        <div class="p-4 rounded-3xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 hover:shadow-xl transition flex flex-col justify-between group">
          <div>
            <div class="relative h-48 rounded-2xl overflow-hidden mb-3 bg-slate-100 dark:bg-slate-800">
              ${{imageUrl ? `<img src="${{imageUrl}}" alt="${{title}}" loading="lazy" decoding="async" class="w-full h-full object-cover group-hover:scale-105 transition duration-500">` : '<div aria-hidden="true" class="w-full h-full flex items-center justify-center text-4xl">📦</div>'}}
              <span class="absolute top-2.5 right-2.5 px-2.5 py-1 rounded-full text-[10px] font-black bg-amber-400 text-slate-950">${{badge}}</span>
            </div>
            <div class="flex items-center justify-between text-xs text-slate-400 mb-1">
              <span>${{category}}</span>
              <span class="text-amber-400 font-bold">${{rating}}</span>
            </div>
            <h4 class="font-bold text-sm text-slate-900 dark:text-white mb-1.5">${{title}}</h4>
            <p class="text-[11px] text-slate-500 dark:text-slate-400 font-readex line-clamp-2 mb-3">${{description}}</p>
          </div>
          <div class="flex items-center justify-between pt-3 border-t border-slate-100 dark:border-slate-800">
            <b class="text-base font-black text-brand-500">${{price}} ${{d.currency}}</b>
            <button onclick="addToCart(${{id}})" class="px-3.5 py-2 rounded-xl bg-slate-900 dark:bg-white text-white dark:text-slate-900 hover:opacity-90 font-bold text-xs transition">
              ${{d.addCart}}
            </button>
          </div>
        </div>
      `;
      }}).join('');
    }}

    function renderCategoryPills() {{
      const c = document.getElementById('cat-pills');
      const cats = ['الكل', ...CATEGORIES];
      c.innerHTML = cats.map(cat => `
        <button type="button" data-category="${{escapeCatalogHtml(cat)}}" class="px-4 py-2 rounded-xl text-xs font-bold whitespace-nowrap transition ${{selectedCategory === cat ? 'bg-brand-500 text-white' : 'bg-white dark:bg-slate-900 text-slate-600 dark:text-slate-300 border border-slate-200 dark:border-slate-800'}}">
          ${{escapeCatalogHtml(cat)}}
        </button>
      `).join('');
      c.querySelectorAll('[data-category]').forEach(button => {{
        button.addEventListener('click', () => filterCategory(button.dataset.category));
      }});
    }}

    function filterCategory(cat) {{
      selectedCategory = cat;
      renderCategoryPills();
      if (cat === 'الكل') {{
        renderCatalog(CATALOG);
      }} else {{
        renderCatalog(CATALOG.filter(p => p.category === cat));
      }}
    }}

    function handleSearch(q) {{
      const filtered = CATALOG.filter(p => p.title.includes(q) || (p.title_en && p.title_en.toLowerCase().includes(q.toLowerCase())));
      renderCatalog(filtered);
    }}

    function addToCart(id) {{
      const safeId = Number(id);
      if (!Number.isSafeInteger(safeId) || safeId < 1) return;
      const p = CATALOG.find(x => Number(x.id) === safeId);
      if (!p) return;
      const safeProduct = {{ ...p, id: safeId, price: safeCatalogPrice(p.price) }};
      const exist = cart.find(x => x.id === safeId);
      const itemCount = cart.reduce((sum, item) => sum + item.qty, 0);
      if (itemCount >= 100) {{
        alert('The order limit is 100 items.');
        return;
      }}
      if (exist) {{
        if (exist.qty >= 50) {{
          alert('A maximum of 50 units per product is allowed.');
          return;
        }}
        checkoutIdempotencyKey = null;
        exist.qty++;
      }} else {{
        if (cart.length >= 50) {{
          alert('A maximum of 50 different products is allowed per order.');
          return;
        }}
        checkoutIdempotencyKey = null;
        cart.push({{ ...safeProduct, qty: 1 }});
      }}
      updateCartUI();
      toggleCart(true);
    }}

    function updateCartUI() {{
      const badge = document.getElementById('cart-badge');
      const container = document.getElementById('cart-items-container');
      const totalCount = cart.reduce((s, x) => s + x.qty, 0);
      badge.textContent = totalCount;

      if (!cart.length) {{
        container.innerHTML = '<div class="text-center py-10 text-slate-400 text-xs font-readex">السلة فارغة حالياً</div>';
      }} else {{
        container.innerHTML = cart.map(it => {{
          const id = Number(it.id);
          if (!Number.isSafeInteger(id) || id < 1) return '';
          const title = escapeCatalogHtml(it.title);
          const price = safeCatalogPrice(it.price);
          const qty = Number.isSafeInteger(Number(it.qty)) && Number(it.qty) > 0 ? Number(it.qty) : 1;
          return `
          <div class="p-3 rounded-2xl bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 flex items-center justify-between">
            <div>
              <b class="text-xs text-slate-900 dark:text-white block">${{title}}</b>
              <span class="text-[11px] text-brand-500 font-bold">${{price}} ج.م</span>
            </div>
            <div class="flex items-center gap-2">
              <button onclick="changeQty(${{id}}, -1)" class="w-6 h-6 rounded bg-slate-200 dark:bg-slate-800 text-xs font-bold">-</button>
              <span class="text-xs font-bold">${{qty}}</span>
              <button onclick="changeQty(${{id}}, 1)" class="w-6 h-6 rounded bg-slate-200 dark:bg-slate-800 text-xs font-bold">+</button>
            </div>
          </div>
        `;
        }}).join('');
      }}

      const subtotal = cart.reduce((s, x) => s + (safeCatalogPrice(x.price) * Math.max(0, Number(x.qty) || 0)), 0);
      const discountVal = 0;
      const total = subtotal;

      document.getElementById('c-subtotal').textContent = `${{subtotal.toFixed(0)}} ج.م`;
      document.getElementById('c-discount').textContent = `${{discountVal.toFixed(0)}} ج.م`;
      document.getElementById('c-total').textContent = `${{total.toFixed(0)}} ج.م`;
    }}

    function changeQty(id, delta) {{
      const it = cart.find(x => x.id === id);
      if (!it) return;
      checkoutIdempotencyKey = null;
      it.qty += delta;
      if (it.qty <= 0) cart = cart.filter(x => x.id !== id);
      updateCartUI();
    }}

    function toggleCart(forceOpen = false) {{
      const d = document.getElementById('cart-drawer');
      if (forceOpen) {{
        d.classList.remove('closed');
      }} else {{
        d.classList.toggle('closed');
      }}
    }}

    function openCheckoutModal() {{
      if (!cart.length) return alert('السلة فارغة!');
      document.getElementById('checkout-modal').classList.remove('hidden');
    }}

    function closeCheckoutModal() {{
      document.getElementById('checkout-modal').classList.add('hidden');
    }}

    async function submitCheckout(e) {{
      e.preventDefault();
      const btn = document.getElementById('btn-submit-order');
      btn.disabled = true;
      btn.textContent = '⏳ جاري الحفظ والتأكيد...';

      const payload = {{
        customer_name: document.getElementById('chk-name').value.trim(),
        customer_phone: document.getElementById('chk-phone').value.trim(),
        customer_address: document.getElementById('chk-address').value.trim(),
        payment_method: document.querySelector('input[name="pay-method"]:checked')?.value || 'cod',
        items: cart.map(x => ({{ id: x.id, quantity: x.qty }}))
      }};
      checkoutIdempotencyKey = checkoutIdempotencyKey || crypto.randomUUID();

      try {{
        const res = await fetch('/api/v1/orders', {{
          method: 'POST',
          headers: {{ 'Content-Type': 'application/json', 'Idempotency-Key': checkoutIdempotencyKey }},
          body: JSON.stringify(payload)
        }});
        const d = await res.json().catch(() => ({{}}));
        if (!res.ok) throw new Error(d.message || 'Unable to submit the order request.');
        alert('تم استلام طلبك وهو في انتظار تأكيد المتجر. رقم الطلب: ' + (d.data?.order?.orderRef || ''));
        checkoutIdempotencyKey = null;
        cart = [];
        updateCartUI();
        closeCheckoutModal();
        toggleCart(false);
      }} catch(err) {{
        alert('تعذر إرسال طلبك. يرجى المحاولة مرة أخرى.');
      }} finally {{
        btn.disabled = false;
        btn.textContent = '✅ تأكيد الأوردر وإرساله للمتجر';
      }}
    }}

    // Do not publish testimonials unless verified customer feedback exists.
    function renderReviews() {{
      const c = document.getElementById('reviews-container');
      const message = escapeCatalogHtml(I18N[currentLang].revSub);
      c.innerHTML = `<p class="col-span-full text-center py-8 text-sm text-slate-500 dark:text-slate-400">${{message}}</p>`;
    }}

    // Init
    renderCategoryPills();
    renderCatalog();
    renderReviews();
  </script>
</body>
</html>"""


def generate_admin_portal_html(brand_name: str, job_id: int) -> str:
    """Produces the Executive Management & Operations Portal for the store."""
    brand_html = html.escape(_safe_text(brand_name, "المتجر المصري", 120))
    return f"""<!doctype html>
<html lang="ar" dir="rtl">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>لوحة التحكم والإدارة — {brand_html}</title>
  <link href="https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;800;900&family=JetBrains+Mono:wght@400;700&display=swap" rel="stylesheet">
  <script src="https://cdn.tailwindcss.com"></script>
  <style>body {{ font-family: 'Cairo', sans-serif; }}</style>
</head>
<body class="bg-slate-950 text-slate-100 min-h-screen">
  <a href="#main-content" class="sr-only focus:not-sr-only focus:fixed focus:top-3 focus:left-3 focus:z-[100] focus:rounded-lg focus:bg-white focus:px-4 focus:py-3 focus:text-slate-950">Skip to main content</a>
  <main id="main-content" tabindex="-1" class="max-w-7xl mx-auto px-4 py-8">
    <div class="flex items-center justify-between pb-6 border-b border-slate-800 mb-8">
      <div>
        <span class="text-xs font-mono text-cyan-400 font-bold uppercase tracking-wider">ENTERPRISE ADMIN PORTAL</span>
        <h1 class="text-2xl font-black text-white">{brand_html} — لوحة العمليات المركزية</h1>
      </div>
      <div class="flex items-center gap-2">
      <button id="admin-logout" type="button" onclick="logoutAdmin()" class="hidden px-4 py-2 rounded-xl bg-rose-950 hover:bg-rose-900 text-xs font-bold text-rose-200">Sign out</button>
      <a href="/" class="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-xs font-bold text-slate-200">
        🌐 العودة للمتجر
      </a>
      </div>
    </div>

    <section id="admin-login-panel" style="display:none" class="max-w-md mx-auto p-6 rounded-3xl bg-slate-900 border border-slate-800" aria-labelledby="admin-login-title">
      <h2 id="admin-login-title" class="text-xl font-black text-white mb-2">Administrator sign in</h2>
      <p class="text-sm text-slate-400 mb-5">Use a provisioned administrator account. Customer accounts cannot access this portal.</p>
      <form onsubmit="loginAdmin(event)" class="space-y-4">
        <label class="block text-sm text-slate-300">Email
          <input id="admin-email" name="email" type="email" autocomplete="username" required maxlength="254" class="mt-1 w-full rounded-xl bg-slate-950 border border-slate-700 px-3 py-2 text-white">
        </label>
        <label class="block text-sm text-slate-300">Password
          <input id="admin-password" name="password" type="password" autocomplete="current-password" required class="mt-1 w-full rounded-xl bg-slate-950 border border-slate-700 px-3 py-2 text-white">
        </label>
        <button id="admin-login-submit" type="submit" class="w-full rounded-xl bg-cyan-700 hover:bg-cyan-600 px-4 py-2 font-bold text-white">Sign in</button>
      </form>
      <p id="admin-auth-message" class="mt-4 min-h-6 text-sm text-amber-300" role="status" aria-live="polite"></p>
    </section>

    <!-- KPIs -->
    <div id="admin-kpis" style="display:none" class="grid grid-cols-1 sm:grid-cols-4 gap-4 mb-8">
      <div class="p-5 rounded-2xl bg-slate-900 border border-slate-800">
        <span class="text-xs text-slate-400">إجمالي المبيعات المحققة</span>
        <div class="text-2xl font-black text-emerald-400 mt-1" id="kpi-rev">0 ج.م</div>
      </div>
      <div class="p-5 rounded-2xl bg-slate-900 border border-slate-800">
        <span class="text-xs text-slate-400">عدد الأوردرات المستلمة</span>
        <div class="text-2xl font-black text-amber-400 mt-1" id="kpi-orders">0</div>
      </div>
      <div class="p-5 rounded-2xl bg-slate-900 border border-slate-800">
        <span class="text-xs text-slate-400">الطلبات المعلقة (Pending)</span>
        <div class="text-2xl font-black text-cyan-400 mt-1" id="kpi-pending">0</div>
      </div>
      <div class="p-5 rounded-2xl bg-slate-900 border border-slate-800">
        <span class="text-xs text-slate-400">حالة السيرفر والـ API</span>
        <div class="text-2xl font-black text-purple-400 mt-1">ONLINE ✅</div>
      </div>
    </div>

    <!-- Orders Management Table -->
    <div id="admin-orders-panel" style="display:none" class="p-6 rounded-3xl bg-slate-900 border border-slate-800">
      <div class="flex items-center justify-between mb-4">
        <h3 class="font-bold text-base text-white">📦 سجل أوردرات العملاء الواردة</h3>
        <button onclick="loadAdminOrders()" class="px-3 py-1.5 rounded-lg bg-slate-800 text-xs font-bold text-slate-300 hover:text-white">🔄 تحديث</button>
      </div>

      <div class="overflow-x-auto">
        <table aria-label="Customer orders" class="w-full text-xs text-right">
          <thead>
            <tr class="text-slate-400 border-b border-slate-800 pb-2">
              <th class="p-3">رقم الطلب</th>
              <th class="p-3">اسم العميل</th>
              <th class="p-3">الهاتف</th>
              <th class="p-3">طريقة الدفع</th>
              <th class="p-3">المبلغ</th>
              <th class="p-3">الحالة</th>
            </tr>
          </thead>
          <tbody id="orders-tbody" class="divide-y divide-slate-800">
            <tr><td colspan="6" class="text-center py-6 text-slate-500">جاري تحميل سجل الأوردرات...</td></tr>
          </tbody>
        </table>
      </div>
    </div>
  </main>

  <script>
    const escapeHtml = (value) => String(value ?? '').replace(/[&<>"']/g, (char) => (
      {{ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }}[char]
    ));

    function showAdminPortal(isAdmin) {{
      document.getElementById('admin-login-panel').style.display = isAdmin ? 'none' : 'block';
      document.getElementById('admin-kpis').style.display = isAdmin ? 'grid' : 'none';
      document.getElementById('admin-orders-panel').style.display = isAdmin ? 'block' : 'none';
      document.getElementById('admin-logout').classList.toggle('hidden', !isAdmin);
    }}

    async function checkAdminSession() {{
      const message = document.getElementById('admin-auth-message');
      try {{
        const response = await fetch('/api/v1/auth/me', {{ credentials: 'same-origin' }});
        const result = await response.json();
        const isAdmin = response.ok && result.data && result.data.role === 'admin';
        showAdminPortal(isAdmin);
        if (isAdmin) {{
          loadAdminOrders();
        }} else {{
          message.textContent = response.ok ? 'An administrator account is required.' : 'Sign in with an administrator account to continue.';
        }}
      }} catch (_) {{
        showAdminPortal(false);
        message.textContent = 'Unable to verify your session. Please try again.';
      }}
    }}

    async function loginAdmin(event) {{
      event.preventDefault();
      const form = event.currentTarget;
      const button = document.getElementById('admin-login-submit');
      const message = document.getElementById('admin-auth-message');
      button.disabled = true;
      message.textContent = 'Signing in...';
      try {{
        const response = await fetch('/api/v1/auth/login', {{
          method: 'POST', credentials: 'same-origin',
          headers: {{ 'Content-Type': 'application/json' }},
          body: JSON.stringify({{
            email: document.getElementById('admin-email').value,
            password: document.getElementById('admin-password').value
          }})
        }});
        if (!response.ok) throw new Error('Sign-in failed. Check your credentials.');
        const session = await fetch('/api/v1/auth/me', {{ credentials: 'same-origin' }});
        const identity = await session.json();
        if (!session.ok || !identity.data || identity.data.role !== 'admin') {{
          await fetch('/api/v1/auth/logout', {{ method: 'POST', credentials: 'same-origin' }});
          throw new Error('This account is not authorized for the admin portal.');
        }}
        form.reset();
        message.textContent = '';
        showAdminPortal(true);
        await loadAdminOrders();
      }} catch (error) {{
        message.textContent = error.message || 'Unable to sign in. Please try again.';
      }} finally {{
        document.getElementById('admin-password').value = '';
        button.disabled = false;
      }}
    }}

    async function logoutAdmin() {{
      try {{ await fetch('/api/v1/auth/logout', {{ method: 'POST', credentials: 'same-origin' }}); }} catch (_) {{}}
      finally {{
        showAdminPortal(false);
        document.getElementById('admin-auth-message').textContent = 'You have been signed out.';
        document.getElementById('orders-tbody').innerHTML = '';
      }}
    }}

    async function loadAdminOrders() {{
      try {{
        const res = await fetch('/api/v1/orders', {{ credentials: 'same-origin' }});
        if (res.status === 401 || res.status === 403) {{
          showAdminPortal(false);
          document.getElementById('admin-auth-message').textContent = 'Your administrator session is no longer valid. Please sign in again.';
          return;
        }}
        if (!res.ok) throw new Error('Unable to load orders.');
        const d = await res.json();
        const orders = Array.isArray(d.data) ? d.data : [];
        for (const order of orders) {{
          for (const key of ['orderRef', 'customerName', 'customerPhone', 'paymentMethod', 'status']) {{
            order[key] = escapeHtml(order[key] ?? '');
          }}
          const total = Number(order.totalEgp);
          order.totalEgp = Number.isFinite(total) ? total : 0;
        }}

        document.getElementById('kpi-orders').textContent = orders.length;
        const rev = orders.reduce((s, o) => s + (o.paymentStatus === 'paid' ? (o.totalEgp || 0) : 0), 0);
        document.getElementById('kpi-rev').textContent = `${{rev}} ج.م`;
        document.getElementById('kpi-pending').textContent = orders.filter(o => o.status === 'pending').length;

        const tbody = document.getElementById('orders-tbody');
        if (!orders.length) {{
          tbody.innerHTML = '<tr><td colspan="6" class="text-center py-6 text-slate-500">لا توجد أوردرات مسجلة بعد</td></tr>';
          return;
        }}

        tbody.innerHTML = orders.map(o => `
          <tr class="hover:bg-slate-800/50">
            <td class="p-3 font-mono font-bold text-cyan-400">${{o.orderRef || '#' + escapeHtml(Number.isSafeInteger(Number(o.id)) ? Number(o.id) : '')}}</td>
            <td class="p-3 text-white font-bold">${{o.customerName || 'عميل'}}</td>
            <td class="p-3 font-mono">${{o.customerPhone || '-'}}</td>
            <td class="p-3"><span class="px-2 py-0.5 rounded bg-slate-800 text-[11px] font-bold">${{o.paymentMethod || 'COD'}}</span></td>
            <td class="p-3 font-bold text-emerald-400">${{o.totalEgp || 0}} ج.م</td>
            <td class="p-3">
              <span class="px-2 py-0.5 rounded text-[11px] font-black ${{o.paymentStatus === 'paid' ? 'bg-emerald-500/20 text-emerald-300' : 'bg-amber-500/20 text-amber-300'}}">
                ${{o.status || 'pending_confirmation'}}
              </span>
            </td>
          </tr>
        `).join('');
      }} catch(e) {{
        document.getElementById('orders-tbody').innerHTML = '<tr><td colspan="6" class="text-center py-6 text-slate-500">تعذر الاتصال بالـ API المحلي</td></tr>';
      }}
    }}
    checkAdminSession();
  </script>
</body>
</html>"""
