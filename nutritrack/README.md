# NutriTrack

Food recognition → shopping list → spend optimisation.

## Stack

| Layer    | Tech                                       |
|----------|--------------------------------------------|
| Backend  | FastAPI · SQLAlchemy · PostgreSQL (SQLite dev) |
| ML       | ViT (nateraw/food) · ResNet50 · USDA API   |
| Auth     | JWT · bcrypt                               |
| Frontend | Next.js 14 · Tailwind CSS · Recharts       |
| Payments | Stripe (config ready, not wired yet)       |

---

## Quick start — Backend

```bash
cd nutritrack

# 1. Create virtual environment
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # macOS/Linux

# 2. Install dependencies
pip install -r requirements.txt

# 3. Copy env file and set your USDA key
cp .env.example .env

# 4. Run database migrations
alembic upgrade head

# 5. Start the API
uvicorn app.main:app --reload
```

API is live at http://localhost:8000
Swagger docs at http://localhost:8000/docs

---

## Quick start — Frontend

```bash
cd nutritrack-web

# 1. Install dependencies
npm install

# 2. Create env file
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local

# 3. Start dev server
npm run dev
```

Frontend is live at http://localhost:3000

---

## API Endpoints

### Auth
| Method | Path              | Description        |
|--------|-------------------|--------------------|
| POST   | /auth/register    | Create account     |
| POST   | /auth/token       | Login → JWT        |
| GET    | /auth/me          | Current user       |

### Food
| Method | Path                  | Description                        |
|--------|-----------------------|------------------------------------|
| POST   | /predict/             | Upload image → food + nutrition    |
| GET    | /predict/history      | Past scans (auth required)         |
| GET    | /ingredients/{food}   | Ingredient list for a food name    |

### Shopping
| Method | Path                              | Description          |
|--------|-----------------------------------|----------------------|
| GET    | /shopping/                        | Get all lists        |
| POST   | /shopping/                        | Create list          |
| DELETE | /shopping/{id}                    | Delete list          |
| POST   | /shopping/{id}/items              | Add item             |
| POST   | /shopping/{id}/items/bulk         | Add multiple items   |
| PATCH  | /shopping/{id}/items/{item_id}    | Update item          |
| DELETE | /shopping/{id}/items/{item_id}    | Delete item          |

### Spending
| Method | Path              | Description                     |
|--------|-------------------|---------------------------------|
| GET    | /spending/        | All trips                       |
| POST   | /spending/        | Log a trip                      |
| GET    | /spending/summary | Totals + top items + chart data |

---

## Moving to PostgreSQL

Change one line in `.env`:

```
DATABASE_URL=postgresql://user:password@localhost:5432/nutritrack
```

Then re-run migrations:

```bash
alembic upgrade head
```

---

## Running tests

```bash
cd nutritrack
pytest tests/ -v
```

---

## Deploying to production

**Backend (Hetzner VPS ~4€/mo):**
```bash
pip install gunicorn
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

**Frontend (Vercel — free tier):**
```bash
# In Vercel dashboard, set environment variable:
NEXT_PUBLIC_API_URL=https://your-api-domain.com
```
