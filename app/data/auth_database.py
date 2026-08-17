from app.data.database import engine, init_db


def get_connection():
    return engine.connect()


def init_auth_db():
    init_db()