import os
os.environ["DATABASE_URL"]="sqlite:///:memory:"
os.environ["SECRET_KEY"]="test"
from app import app,db,ensure_seed
def client():
 app.config["TESTING"]=True
 with app.app_context(): db.drop_all();ensure_seed()
 return app.test_client()
def test_health():
 r=client().get("/api/health");assert r.status_code==200;assert r.get_json()["status"]=="healthy"
def test_login_page():
 r=client().get("/login");assert r.status_code==200;assert b"Secure sign in" in r.data
