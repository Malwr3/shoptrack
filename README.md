# ShopTrack

A simple inventory and sales system for small shops (dukas, pharmacies, hardware stores). ShopTrack tracks what a shop has in stock, records what it sells, and flags what needs reordering.

Built with **Python, Flask and SQLite**, with Bootstrap for the UI. No external services or payment APIs are required.

> A working demo beats an ambitious project that never gets finished.

---

## Table of Contents

- [Features](#features)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
- [Default Accounts](#default-accounts)
- [Usage Walkthrough](#usage-walkthrough)
- [Roles and Permissions](#roles-and-permissions)
- [Routes](#routes)
- [Database Schema](#database-schema)
- [Project Status and Roadmap](#project-status-and-roadmap)
- [Security Notes](#security-notes)

---

## Features

**Implemented**

- **Login and roles**: session-based login with `admin`, `manager` and `cashier` roles.
- **Dashboard**: today's sales total and transaction count, low-stock alert count, a list of low-stock items, and the five most recent sales.
- **Product management**: add products (SKU, name, category, buying price, selling price, quantity, reorder level) and list or search them by name.
- **Stock-in**: record a delivery from a supplier; the product quantity increases automatically.
- **Sales screen**: pick products, build a cart, choose a payment method (Cash, M-Pesa or Card) and complete the sale. Stock is deducted automatically.
- **Receipts**: a receipt page is shown after every sale, with a Print button (uses the browser's print dialog).
- **Low-stock alerts**: products at or below their reorder level are surfaced on the dashboard.

**Planned** (see [Roadmap](#project-status-and-roadmap))

- Edit and delete products
- Daily sales and best-selling items reports
- Optional extras: sales chart, expiry tracking, M-Pesa integration, forecasting

---

## Tech Stack

| Tool | Used for |
|------|----------|
| Python 3 | Core language |
| Flask 3.1 | Web framework |
| SQLite | Database (file-based, no server needed) |
| Jinja2 + Bootstrap 5.3 (CDN) | Server-rendered screens |
| ReportLab 4.2 | Listed in `requirements.txt` for PDF receipts (not yet used in code) |

---

## Project Structure

```
shoptrack1/
├── run.py                  # Entry point: creates and runs the Flask app
├── requirements.txt        # Python dependencies
├── credentials.txt         # Demo login details (see Security Notes)
├── ShopTrack_Project_Pitch.pdf   # Original project pitch and plan
├── app/
│   ├── __init__.py         # App factory: config, DB init, blueprint registration
│   ├── models.py           # SQLite connection helpers and schema/seed data
│   ├── routes.py           # All routes (auth, products, sales, receipts, stock-in)
│   └── templates/
│       ├── base.html       # Layout, navbar, flash messages
│       ├── login.html
│       ├── dashboard.html
│       ├── products.html
│       ├── add_product.html
│       ├── stock_in.html
│       ├── sales.html      # Product grid + cart
│       └── receipt.html
└── instance/
    └── shoptrack.db        # SQLite database (auto-created on first run)
```

---

## Getting Started

### Prerequisites

- Python 3.10 or newer
- `pip`

### Installation

```bash
# 1. Clone the repository
git clone <your-repo-url>
cd shoptrack1

# 2. Create and activate a virtual environment
python -m venv venv
source venv/bin/activate        # macOS / Linux
venv\Scripts\activate           # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the app
python run.py
```

Open **http://127.0.0.1:5000** in your browser.

On first run the app creates `instance/shoptrack.db`, builds all tables, and seeds two users and three categories (Groceries, Drinks, Household). To reset everything, stop the app and delete `instance/shoptrack.db`.

---

## Default Accounts

| Username | Password | Role |
|----------|----------|------|
| `admin` | `admin123` | admin |
| `jane.cashier` | `password123` | cashier |

These are demo credentials. Change them before any real use.

---

## Usage Walkthrough

The database starts with **no products**, so a typical first session looks like this:

1. **Log in** as `admin`.
2. Go to **Products → + Add Product** and create a few items with a quantity and reorder level.
3. Open **New Sale**, click **+ Add** on products to build a cart, choose a payment method and click **Complete Sale**.
4. View the **receipt**, then print it if needed.
5. Go back to **Home** to see today's sales and any low-stock alerts.
6. When new goods arrive, use the **Stock-in** page (`/stock-in`) to record the delivery and increase quantities.

---

## Roles and Permissions

| Action | Admin | Manager | Cashier |
|--------|:-----:|:-------:|:-------:|
| View dashboard and products | ✅ | ✅ | ✅ |
| Make sales / view receipts | ✅ | ✅ | ✅ |
| Add products | ✅ | ✅ | ❌ |
| Record stock-in | ✅ | ✅ | ❌ |

Only `admin` and `cashier` users are seeded. There is no user-management screen yet, so a `manager` must be inserted directly into the database.

---

## Routes

| Method | Path | Description | Access |
|--------|------|-------------|--------|
| GET | `/` | Dashboard | Logged in |
| GET, POST | `/login` | Sign in | Public |
| GET | `/logout` | Sign out | Any |
| GET | `/products?search=` | List / search products | Logged in |
| GET, POST | `/products/add` | Add a product | Admin, Manager |
| GET, POST | `/sales` | Cart and checkout (`action` = `add`, `clear`, `complete`) | Logged in |
| GET | `/receipt/<sale_id>` | Receipt for a sale | Public (see notes) |
| GET, POST | `/stock-in` | Receive stock from a supplier | Admin, Manager |

---

## Database Schema

SQLite, created automatically by `models.init_db()`.

| Table | Key columns |
|-------|-------------|
| `categories` | `id`, `name` (unique) |
| `suppliers` | `id`, `name` |
| `users` | `id`, `username` (unique), `password`, `role` (`admin` / `manager` / `cashier`) |
| `products` | `id`, `sku` (unique), `name`, `category_id`, `buying_price`, `selling_price`, `quantity`, `reorder_level` |
| `sales` | `id`, `receipt_no` (unique), `cashier_id`, `subtotal`, `discount`, `total`, `payment_method`, `created_at` |
| `sale_items` | `id`, `sale_id`, `product_id`, `quantity`, `price` |

Relationships: `products.category_id → categories.id`, `sales.cashier_id → users.id`, `sale_items.sale_id → sales.id`, `sale_items.product_id → products.id`.

---

## Project Status and Roadmap

The build follows the plan in `ShopTrack_Project_Pitch.pdf`.

**Phase 1: Core build**
- [x] Setup, database and tables
- [x] Login and roles
- [~] Product management (add and list/search done; **edit and delete still to do**)
- [x] Stock updates
- [x] Sales screen with automatic stock deduction
- [x] Printable receipt

**Phase 2: Polish**
- [x] Low-stock alerts on the dashboard
- [ ] Reports: daily sales total and best-selling items
- [ ] Sample data, testing and demo prep

**Phase 3: Optional extras**
- [ ] Sales chart on the dashboard
- [ ] Expiry date tracking
- [ ] M-Pesa payment integration
- [ ] Sales forecasting
- [ ] PDF receipts via ReportLab

### Known gaps

- The sales form has no discount field yet (the backend supports one and defaults it to 0).
- Stock is not checked at checkout, so quantities can go negative.
- Stock-in creates a new `suppliers` row on every delivery rather than reusing existing suppliers.
- The Stock-in page has no navbar link; it is reached at `/stock-in`.
- Receipt numbers are generated with Python's `hash()`, which is not stable across runs and can collide. A sequential or UUID-based number would be safer.
- Bootstrap is loaded from a CDN, so the UI needs an internet connection.

---

## Security Notes

This is a learning/demo project and is **not production-ready** as it stands. Before deploying anywhere real:

- **Passwords are stored in plain text** and compared directly. Use `werkzeug.security.generate_password_hash` / `check_password_hash`.
- **`SECRET_KEY` is hard-coded to `'dev'`.** Load a strong random value from an environment variable.
- **`credentials.txt` contains demo passwords** and is committed to the repo. Remove it and rotate the passwords.
- **`debug=True`** is set in `run.py`. Disable it in production and serve with a WSGI server such as Gunicorn.
- There is **no CSRF protection** on forms.
- `/receipt/<id>` does not require login, so anyone with a receipt ID can view it.
- `instance/` (including the database) is git-ignored, which is correct. Keep it that way.

---

## Contributing

1. Fork the repo and create a feature branch.
2. Finish one step fully before starting the next, as in the project plan.
3. Open a pull request describing the change.

## License

No license has been specified yet. Add a `LICENSE` file (for example MIT) before publishing.
