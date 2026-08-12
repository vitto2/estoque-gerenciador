import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
INSTANCE_DIR = os.path.join(BASE_DIR, "instance")

# Vercel's project root is read-only; only /tmp is writable at runtime
DB_DIR = "/tmp" if os.environ.get("VERCEL") else INSTANCE_DIR


def _database_url():
    url = os.environ.get("DATABASE_URL")
    if url:
        # SQLAlchemy requires 'postgresql://' but Supabase provides 'postgres://'
        return url.replace("postgres://", "postgresql://", 1)
    return f"sqlite:///{os.path.join(DB_DIR, 'estoque.db')}"


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "troque-esta-chave-em-producao")
    SQLALCHEMY_DATABASE_URI = _database_url()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
