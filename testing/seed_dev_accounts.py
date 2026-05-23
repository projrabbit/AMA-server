"""
Seed / reset test accounts with real password hashes.

Run:
    uv run python testing/seed_dev_accounts.py

Accounts created / updated:
    username                  password        role
    linh.tran@example.com     Admin@2026      admin
    minh.nguyen@example.com   Employee@2026   employee
    hoa.pham@example.com      Hr@2026xx       hr
    quang.le@example.com      Manager@2026    manager
"""
import os
import sys

# make sure project root is on the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sqlalchemy import create_engine, text
from dotenv import load_dotenv

from app.core.security import get_password_hash

load_dotenv()

from sqlalchemy import URL
database_url = URL.create(
    drivername=os.getenv("DATABASE_DRIVER", "postgresql+psycopg"),
    username=os.getenv("DATABASE_USER", "postgres"),
    password=os.getenv("DATABASE_PASSWORD", ""),
    host=os.getenv("DATABASE_HOST", "localhost"),
    port=int(os.getenv("DATABASE_PORT", "5432")),
    database=os.getenv("DATABASE_NAME", "postgres"),
    query={"sslmode": os.getenv("DATABASE_SSL_MODE", "require")},
)

ACCOUNTS = [
    # (account_id, username, password, role)
    (1001, "linh.tran@example.com",   "Admin@2026",    "admin"),
    (1002, "minh.nguyen@example.com", "Employee@2026", "employee"),
    (1003, "hoa.pham@example.com",    "Hr@2026xx",     "hr"),
    (1004, "quang.le@example.com",    "Manager@2026",  "manager"),
]

engine = create_engine(database_url)

with engine.begin() as conn:
    for account_id, username, password, role in ACCOUNTS:
        hashed = get_password_hash(password)
        conn.execute(
            text("""
                UPDATE business.account
                SET password_hash = :hash,
                    is_active     = true
                WHERE account_id = :id
            """),
            {"hash": hashed, "id": account_id},
        )
        print(f"  OK [{role:8s}] {username}  ->  password: {password}")

print("\nSeed done. Login on Swagger with the accounts above.")
