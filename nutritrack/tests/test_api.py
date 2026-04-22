"""
Run with: pytest tests/ -v
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database import Base, get_db

# ── In-memory SQLite for tests ─────────────────────────────────────────────────
TEST_DB = "sqlite:///./test_nutritrack.db"
engine  = create_engine(TEST_DB, connect_args={"check_same_thread": False})
TestSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestSession()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True, scope="module")
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


client = TestClient(app)

# ── Helpers ───────────────────────────────────────────────────────────────────

def register_and_login(email="test@example.com", password="password123"):
    client.post("/auth/register", json={"email": email, "password": password, "full_name": "Test User"})
    resp = client.post("/auth/token", data={"username": email, "password": password})
    return resp.json()["access_token"]


# ── Auth ──────────────────────────────────────────────────────────────────────

def test_register():
    resp = client.post("/auth/register", json={
        "email": "newuser@example.com", "password": "pass1234"
    })
    assert resp.status_code == 201
    assert resp.json()["email"] == "newuser@example.com"


def test_register_duplicate():
    client.post("/auth/register", json={"email": "dup@example.com", "password": "abc"})
    resp = client.post("/auth/register", json={"email": "dup@example.com", "password": "abc"})
    assert resp.status_code == 400


def test_login():
    client.post("/auth/register", json={"email": "login@example.com", "password": "pass"})
    resp = client.post("/auth/token", data={"username": "login@example.com", "password": "pass"})
    assert resp.status_code == 200
    assert "access_token" in resp.json()


def test_login_wrong_password():
    resp = client.post("/auth/token", data={"username": "login@example.com", "password": "wrong"})
    assert resp.status_code == 401


# ── Shopping lists ─────────────────────────────────────────────────────────────

def test_create_and_get_list():
    token = register_and_login("shop@example.com", "pass1234")
    headers = {"Authorization": f"Bearer {token}"}

    # Create
    resp = client.post("/shopping/", json={"name": "Weekly Shop"}, headers=headers)
    assert resp.status_code == 201
    list_id = resp.json()["id"]

    # Get all lists
    resp = client.get("/shopping/", headers=headers)
    assert resp.status_code == 200
    assert any(l["id"] == list_id for l in resp.json())


def test_add_and_update_item():
    token = register_and_login("items@example.com", "pass1234")
    headers = {"Authorization": f"Bearer {token}"}

    lst = client.post("/shopping/", json={"name": "Test"}, headers=headers).json()
    list_id = lst["id"]

    # Add item
    resp = client.post(f"/shopping/{list_id}/items", json={
        "name": "Milk", "quantity": 2, "unit": "l",
        "category": "dairy", "estimated_price": 2.50
    }, headers=headers)
    assert resp.status_code == 201
    item_id = resp.json()["id"]

    # Update — mark checked, add actual price
    resp = client.patch(f"/shopping/{list_id}/items/{item_id}",
                        json={"is_checked": True, "actual_price": 2.40}, headers=headers)
    assert resp.status_code == 200
    assert resp.json()["is_checked"] is True
    assert resp.json()["actual_price"] == 2.40


def test_bulk_add_items():
    token = register_and_login("bulk@example.com", "pass1234")
    headers = {"Authorization": f"Bearer {token}"}

    lst = client.post("/shopping/", json={"name": "Bulk"}, headers=headers).json()
    list_id = lst["id"]

    items = [
        {"name": "Flour",  "quantity": 1, "unit": "kg", "category": "grains"},
        {"name": "Eggs",   "quantity": 12, "unit": "pcs", "category": "other"},
        {"name": "Butter", "quantity": 250, "unit": "g", "category": "dairy"},
    ]
    resp = client.post(f"/shopping/{list_id}/items/bulk", json=items, headers=headers)
    assert resp.status_code == 201
    assert len(resp.json()) == 3


# ── Spending ───────────────────────────────────────────────────────────────────

def test_log_spending_and_summary():
    token = register_and_login("spend@example.com", "pass1234")
    headers = {"Authorization": f"Bearer {token}"}

    payload = {
        "store_name":  "Kaufland",
        "total_spent": 45.80,
        "currency":    "BGN",
        "items": [
            {"name": "chicken", "qty": 1, "price": 12.50},
            {"name": "vegetables", "qty": 3, "price": 5.00},
        ]
    }
    resp = client.post("/spending/", json=payload, headers=headers)
    assert resp.status_code == 201

    summary = client.get("/spending/summary", headers=headers).json()
    assert summary["num_trips"] == 1
    assert summary["total_spent"] == 45.80


# ── Ingredients endpoint ───────────────────────────────────────────────────────

def test_get_ingredients_known_food():
    resp = client.get("/ingredients/pizza")
    assert resp.status_code == 200
    data = resp.json()
    assert "pizza" in data["food_name"]
    assert len(data["ingredients"]) > 0


def test_get_ingredients_unknown_food():
    resp = client.get("/ingredients/xyzunknownfood123")
    assert resp.status_code == 200
    assert resp.json()["ingredients"] == []


# ── Health check ──────────────────────────────────────────────────────────────

def test_health_check():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"
