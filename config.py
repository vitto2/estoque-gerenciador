import os

from sqlalchemy.pool import NullPool

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


_DATABASE_URL = _database_url()
_IS_POSTGRES = _DATABASE_URL.startswith("postgresql")


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "troque-esta-chave-em-producao")
    SQLALCHEMY_DATABASE_URI = _DATABASE_URL
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Extração do número de série a partir de foto (OpenAI Vision).
    # Sem essa chave configurada, o recurso fica desativado de forma graciosa.
    OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
    OPENAI_VISION_MODEL = os.environ.get("OPENAI_VISION_MODEL", "gpt-4o-mini")

    # Cada invocação serverless é curta e isolada; sem um pool sobrevivendo
    # entre requisições, o QueuePool padrão do SQLAlchemy tende a acumular
    # conexões que nunca são fechadas e esgotam o limite do Postgres.
    # NullPool abre e fecha a conexão a cada request, e pool_pre_ping evita
    # erros por conexões que o servidor já derrubou por inatividade.
    if _IS_POSTGRES:
        SQLALCHEMY_ENGINE_OPTIONS = {
            "poolclass": NullPool,
            "pool_pre_ping": True,
        }
