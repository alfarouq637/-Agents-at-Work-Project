---
roles: Frontend Developer, Full-Stack Developer, Solutions Architect, UI Designer, UX Planner
tools: calc, fetch_url
---
# Full-Stack SME Web Applications Specification

When building a full-stack digital product for an Egyptian SME:
1. **Architecture (Frontend + Backend Integration)**:
   - The application MUST be fully interactive and connected to its dedicated AutoCorp Backend API.
   - Use `const SITE_ID = window.SITE_ID || '1';` and `const API_BASE = window.location.origin + '/api/sites/' + SITE_ID;`.
   - The frontend must dynamically fetch its items/menu via `GET ${API_BASE}/items` (with fallback to embedded initial items).
   - Orders/Bookings MUST submit to `POST ${API_BASE}/orders` with payload: `{ customer_name, customer_phone, customer_address, items, total_egp, payment_method }`.
   - On success, display an interactive Order Confirmation Receipt with reference number and delivery tracker.

2. **Egyptian Payment Gateways Layer**:
   - Offer an interactive, professional checkout modal supporting Egyptian SME payment methods:
     a) **Vodafone Cash / محافظ إلكترونية**: Display SME wallet number with instant copy button and transaction ref input.
     b) **Fawry Pay (فوري)**: Generates instant 8-digit Fawry reference code for kiosk payment.
     c) **InstaPay (إنستاباي)**: One-click IPA transfer address.
     d) **Visa / Mastercard (Paymob Card)**: Secure card input with SSL badge.
     e) **الدفع عند الاستلام (Cash on Delivery)**.

3. **High-End UI/UX Design System**:
   - Fonts: Import `<link href="https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;900&family=Readex+Pro:wght@400;600;700&display=swap" rel="stylesheet">`.
   - Palette: Warm Egyptian luxury (Terracotta `#C0392B`, Gold `#D4AF37`, Emerald, Deep Slate `#0F172A`).
   - Micro-interactions: Floating WhatsApp action button, live cart badge counter, filter pills, smooth category scrolling.
   - Accessibility: Full Arabic `dir="rtl" lang="ar"`, accessible contrast, mobile-first responsive layout.
