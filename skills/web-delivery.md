---
roles: Frontend Developer, Solutions Architect, UX Planner, UI Designer, Code Reviewer
tools: calc
---
# Modern Egyptian SME Web & UI/UX Standards

Websites generated MUST be complete, production-grade web applications:
- **Design System**: Arabic RTL (`dir="rtl" lang="ar"`), modern Tailwind CSS, typography: Cairo + Readex Pro.
- **Sections Required**:
  1. Sticky Glassmorphism Navbar with Logo, Navigation links, and live Cart/Order button.
  2. Hero Section with dynamic value proposition, badge, and primary CTA.
  3. Interactive Menu / Services catalog with category filtering tabs and "Add to Cart / Book" buttons.
  4. About & Authenticity section highlighting local Egyptian quality and craftsmanship.
  5. Customer Reviews & Social Proof with verified Egyptian ratings.
  6. Interactive Checkout / Order Modal supporting Vodafone Cash, Fawry Pay, InstaPay, Visa/Mastercard, and Cash.
  7. Footer with delivery zones, operating hours, phone, and floating WhatsApp shortcut.
- **Backend Communication**:
  - Connect to backend API: `POST /api/sites/{site_id}/orders` and `GET /api/sites/{site_id}/items`.
  - Handle loading states, error toasts, and instant order confirmation popups.
- **Strict Quality**: No broken markup, fully closed tags, mobile responsive drawer.
