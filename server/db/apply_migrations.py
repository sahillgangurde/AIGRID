"""
Unified Database Migration and Synchronization Utility.
Supports both SQLite (local development) and PostgreSQL / Supabase (production cloud).
Reads connection strings and credentials from the root .env file.
"""

import os
import sys
import argparse
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import text

# Add root directory to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from server.db.session import engine, SessionLocal, Base, DATABASE_URL
import server.db.models as models
from server.seed.seed_data import seed_database

MIGRATIONS_DIR = Path(__file__).resolve().parent.parent.parent / "supabase" / "migrations"
SEED_SQL_PATH = Path(__file__).resolve().parent.parent.parent / "supabase" / "seed.sql"

def ensure_sqlite_columns():
    """Ensure newly introduced columns exist in SQLite if tables were created previously."""
    if not DATABASE_URL.startswith("sqlite"):
        return
    with engine.connect() as conn:
        # Check projects table for identity_revealed
        try:
            res = conn.execute(text("PRAGMA table_info(projects)")).fetchall()
            col_names = [r[1] for r in res]
            if "identity_revealed" not in col_names:
                conn.execute(text("ALTER TABLE projects ADD COLUMN identity_revealed BOOLEAN DEFAULT 0"))
                conn.commit()
                print("[OK] Added missing column `identity_revealed` to `projects` table.")
        except Exception as e:
            print(f"! Notice on checking table_info(projects): {e}")

        # Subscription free-trial columns (CreatorGrid revenue model)
        try:
            res = conn.execute(text("PRAGMA table_info(subscriptions)")).fetchall()
            col_names = [r[1] for r in res]
            if "trial_start" not in col_names:
                conn.execute(text("ALTER TABLE subscriptions ADD COLUMN trial_start DATETIME"))
                print("[OK] Added column `trial_start` to `subscriptions` table.")
            if "trial_end" not in col_names:
                conn.execute(text("ALTER TABLE subscriptions ADD COLUMN trial_end DATETIME"))
                print("[OK] Added column `trial_end` to `subscriptions` table.")
            if "is_listed" not in col_names:
                conn.execute(text("ALTER TABLE subscriptions ADD COLUMN is_listed BOOLEAN DEFAULT 1"))
                print("[OK] Added column `is_listed` to `subscriptions` table.")
            conn.commit()
        except Exception as e:
            print(f"! Notice on checking table_info(subscriptions): {e}")

def run_sqlite_sync(seed: bool = False):
    print("=== Initializing SQLite Database ===")
    Base.metadata.create_all(bind=engine)
    ensure_sqlite_columns()
    print("[OK] All SQLAlchemy tables verified/created.")

    if seed:
        print("=== Seeding Initial Data ===")
        db = SessionLocal()
        try:
            seed_database(db)
            print("[OK] Database successfully seeded with demo creators, briefs, and projects.")
        finally:
            db.close()

def run_postgres_migrations(seed: bool = False):
    print("=== Running PostgreSQL / Supabase Migrations ===")
    migration_files = sorted(MIGRATIONS_DIR.glob("*.sql"))
    if not migration_files:
        print("! No SQL migration files found in supabase/migrations/")
        return

    with engine.connect() as conn:
        for sql_file in migration_files:
            print(f"Applying migration: {sql_file.name}...")
            content = sql_file.read_text(encoding="utf-8")
            # Execute migration statements
            try:
                conn.execute(text(content))
                conn.commit()
                print(f"[OK] Migration {sql_file.name} applied successfully.")
            except Exception as e:
                print(f"! Error or notice applying {sql_file.name}: {e}")
                conn.rollback()

        if seed and SEED_SQL_PATH.exists():
            print("=== Applying Supabase seed.sql ===")
            seed_content = SEED_SQL_PATH.read_text(encoding="utf-8")
            try:
                conn.execute(text(seed_content))
                conn.commit()
                print("[OK] seed.sql applied successfully.")
            except Exception as e:
                print(f"! Error applying seed.sql: {e}")
                conn.rollback()

def main():
    parser = argparse.ArgumentParser(description="Synchronize and apply database migrations.")
    parser.add_argument("--seed", action="store_true", help="Seed default demo data into the database")
    args = parser.parse_args()

    print(f"Connected to database at: {DATABASE_URL.split('@')[-1] if '@' in DATABASE_URL else DATABASE_URL}")

    if DATABASE_URL.startswith("sqlite"):
        run_sqlite_sync(seed=args.seed)
    else:
        run_postgres_migrations(seed=args.seed)
    print("=== Database synchronization complete ===")

if __name__ == "__main__":
    main()
