import sqlite3

from app.core.security import (
    create_access_token,
    hash_password,
    verify_password,
)
from app.data.auth_database import get_connection


def create_user(name: str, email: str, password: str):
    email = email.strip().lower()

    connection = get_connection()

    try:
        existing_user = connection.execute(
            "SELECT id FROM users WHERE email = ?",
            (email,),
        ).fetchone()

        if existing_user:
            raise ValueError("An account with this email already exists.")

        password_hash = hash_password(password)

        cursor = connection.execute(
            """
            INSERT INTO users (
                name,
                email,
                password_hash
            )
            VALUES (?, ?, ?)
            """,
            (
                name.strip(),
                email,
                password_hash,
            ),
        )

        connection.commit()

        user_id = cursor.lastrowid

        return {
            "id": user_id,
            "name": name.strip(),
            "email": email,
        }

    except sqlite3.IntegrityError:
        connection.rollback()
        raise ValueError("An account with this email already exists.")

    finally:
        connection.close()


def authenticate_user(email: str, password: str):
    email = email.strip().lower()

    connection = get_connection()

    try:
        user = connection.execute(
            """
            SELECT
                id,
                name,
                email,
                password_hash
            FROM users
            WHERE email = ?
            """,
            (email,),
        ).fetchone()

        if not user:
            return None

        if not verify_password(
            password,
            user["password_hash"],
        ):
            return None

        return {
            "id": user["id"],
            "name": user["name"],
            "email": user["email"],
        }

    finally:
        connection.close()


def login_user(email: str, password: str):
    user = authenticate_user(email, password)

    if not user:
        return None

    token = create_access_token(
        user_id=user["id"],
        email=user["email"],
    )

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": user,
    }


def get_user_by_id(user_id: int):
    connection = get_connection()

    try:
        user = connection.execute(
            """
            SELECT
                id,
                name,
                email
            FROM users
            WHERE id = ?
            """,
            (user_id,),
        ).fetchone()

        if not user:
            return None

        return {
            "id": user["id"],
            "name": user["name"],
            "email": user["email"],
        }

    finally:
        connection.close()