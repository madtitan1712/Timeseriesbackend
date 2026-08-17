from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from app.core.security import create_access_token, hash_password, verify_password
from app.data.database import engine


def create_user(name: str, email: str, password: str):
    email = email.strip().lower()
    password_hash = hash_password(password)

    try:
        with engine.begin() as conn:
            result = conn.execute(
                text("""INSERT INTO users (name, email, password_hash)
                        VALUES (:name, :email, :password_hash) RETURNING id"""),
                {"name": name.strip(), "email": email, "password_hash": password_hash},
            )
            user_id = result.scalar_one()
    except IntegrityError:
        raise ValueError("An account with this email already exists.")

    return {"id": user_id, "name": name.strip(), "email": email}


def authenticate_user(email: str, password: str):
    email = email.strip().lower()
    with engine.connect() as conn:
        row = conn.execute(
            text("SELECT id, name, email, password_hash FROM users WHERE email = :email"),
            {"email": email},
        ).mappings().first()

    if not row or not verify_password(password, row["password_hash"]):
        return None
    return {"id": row["id"], "name": row["name"], "email": row["email"]}


def login_user(email: str, password: str):
    user = authenticate_user(email, password)
    if not user:
        return None
    token = create_access_token(user_id=user["id"], email=user["email"])
    return {"access_token": token, "token_type": "bearer", "user": user}


def get_user_by_id(user_id: int):
    with engine.connect() as conn:
        row = conn.execute(
            text("SELECT id, name, email FROM users WHERE id = :id"), {"id": user_id}
        ).mappings().first()
    if not row:
        return None
    return {"id": row["id"], "name": row["name"], "email": row["email"]}