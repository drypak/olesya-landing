from app.auth import hash_password
from app.db import get_connection


def init_db() -> None:
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS admin_users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            hashed_password TEXT NOT NULL,
            is_active INTEGER NOT NULL DEFAULT 1
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS leads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            contact TEXT NOT NULL,
            service TEXT NOT NULL,
            comment TEXT,
            status TEXT NOT NULL DEFAULT 'new',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    cur.execute("SELECT id FROM admin_users WHERE username = ?", ("admin",))
    admin = cur.fetchone()

    if admin is None:
        cur.execute(
            """
            INSERT INTO admin_users (username, hashed_password, is_active)
            VALUES (?, ?, ?)
            """,
            ("admin", hash_password("admin123"), 1),
        )

    conn.commit()
    conn.close()


if __name__ == "__main__":
    init_db()
    print("Database initialized")