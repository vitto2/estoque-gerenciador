import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
INSTANCE_DIR = os.path.join(BASE_DIR, "instance")

# Vercel's project root is read-only; only /tmp is writable at runtime
DB_DIR = "/tmp" if os.environ.get("VERCEL") else INSTANCE_DIR


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "troque-esta-chave-em-producao")
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{os.path.join(DB_DIR, 'estoque.db')}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
