import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), "..", "..", "server", "data", "frame.db")
if not os.path.exists(db_path):
    db_path = "server/data/frame.db"

con = sqlite3.connect(db_path)
cur = con.cursor()

tables_cols = {
    "creative_briefs": [
        ("is_confidential", "BOOLEAN DEFAULT 0"),
        ("masked_brand_name", "TEXT DEFAULT 'Confidential Brand Partner'")
    ],
    "brand_profiles": [
        ("public_alias", "TEXT"),
        ("is_confidential", "BOOLEAN DEFAULT 0"),
        ("masked_brand_name", "TEXT DEFAULT 'Confidential Brand Partner'")
    ],
    "projects": [
        ("creator_quote_amount", "REAL"),
        ("markup_percent", "REAL DEFAULT 0.20"),
        ("brand_payable_amount", "REAL"),
        ("advance_amount", "REAL"),
        ("escrow_state", "TEXT DEFAULT 'pending_advance'"),
        ("advance_locked_at", "DATETIME"),
        ("contact_unlocked_at", "DATETIME")
    ],
    "disputes": [
        ("ai_audit_report", "TEXT"),
        ("ai_recommended_action", "TEXT"),
        ("ai_confidence_score", "REAL")
    ]
}

for table, cols in tables_cols.items():
    try:
        cur.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'")
        if not cur.fetchone():
            continue
        existing = [r[1] for r in cur.execute(f"PRAGMA table_info({table})").fetchall()]
        for col_name, col_type in cols:
            if col_name not in existing:
                cur.execute(f"ALTER TABLE {table} ADD COLUMN {col_name} {col_type}")
                print(f"Added {col_name} to {table}")
    except Exception as e:
        print(f"Error on {table}: {e}")

con.commit()
con.close()
print("Migration completed.")
