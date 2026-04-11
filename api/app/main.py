from typing import Optional

from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware

from app.auth import create_access_token, decode_access_token, verify_password
from app.db import get_connection
from app.init_db import init_db
from app.schemas import LeadCreate, LeadOut, LeadStatusUpdate, LoginInput, TokenOut

app = FastAPI(title="Olesya API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

init_db()


def require_admin_token(authorization: Optional[str]) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Требуется токен")

    token = authorization.replace("Bearer ", "", 1)
    payload = decode_access_token(token)

    if not payload or "sub" not in payload:
        raise HTTPException(status_code=401, detail="Неверный токен")

    return payload["sub"]


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.post("/api/auth/login", response_model=TokenOut)
def login(data: LoginInput):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        "SELECT username, hashed_password, is_active FROM admin_users WHERE username = ?",
        (data.username,),
    )
    user = cur.fetchone()
    conn.close()

    if not user:
        raise HTTPException(status_code=401, detail="Неверный логин или пароль")

    if not user["is_active"]:
        raise HTTPException(status_code=403, detail="Пользователь отключён")

    if not verify_password(data.password, user["hashed_password"]):
        raise HTTPException(status_code=401, detail="Неверный логин или пароль")

    token = create_access_token({"sub": user["username"]})
    return TokenOut(access_token=token)


@app.post("/api/leads", response_model=LeadOut)
def create_lead(data: LeadCreate):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO leads (name, contact, service, comment)
        VALUES (?, ?, ?, ?)
        """,
        (data.name, data.contact, data.service, data.comment),
    )

    lead_id = cur.lastrowid
    conn.commit()

    cur.execute("SELECT * FROM leads WHERE id = ?", (lead_id,))
    row = cur.fetchone()
    conn.close()

    return LeadOut(**dict(row))


@app.get("/api/leads", response_model=list[LeadOut])
def list_leads(authorization: Optional[str] = Header(default=None)):
    require_admin_token(authorization)

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM leads ORDER BY created_at DESC")
    rows = cur.fetchall()
    conn.close()

    return [LeadOut(**dict(row)) for row in rows]


@app.patch("/api/leads/{lead_id}", response_model=LeadOut)
def update_lead_status(
    lead_id: int,
    data: LeadStatusUpdate,
    authorization: Optional[str] = Header(default=None),
):
    require_admin_token(authorization)

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT * FROM leads WHERE id = ?", (lead_id,))
    existing = cur.fetchone()

    if not existing:
        conn.close()
        raise HTTPException(status_code=404, detail="Заявка не найдена")

    cur.execute(
        "UPDATE leads SET status = ? WHERE id = ?",
        (data.status, lead_id),
    )
    conn.commit()

    cur.execute("SELECT * FROM leads WHERE id = ?", (lead_id,))
    updated = cur.fetchone()
    conn.close()

    return LeadOut(**dict(updated))