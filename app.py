import os

from flask import Flask, render_template
from flask_wtf import CSRFProtect

from config import Config, DB_DIR
from models import db, status_descricao, status_slug

csrf = CSRFProtect()


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    os.makedirs(DB_DIR, exist_ok=True)

    db.init_app(app)
    csrf.init_app(app)
    app.jinja_env.globals["status_descricao"] = status_descricao
    app.jinja_env.globals["status_slug"] = status_slug

    @app.context_processor
    def injetar_alerta_banco():
        # Em produção (Vercel) sem DATABASE_URL configurada, o app cai pra
        # SQLite efêmero — cada instância serverless tem seu próprio arquivo
        # e os dados "somem" de forma imprevisível. Esse alerta aparece em
        # toda página até a variável ser configurada corretamente.
        sem_persistencia = app.config.get("IS_VERCEL") and not app.config.get("IS_POSTGRES")
        return {"banco_sem_persistencia": sem_persistencia}

    with app.app_context():
        db.create_all()

    from routes.dashboard import dashboard_bp
    from routes.equipamentos import equipamentos_bp

    app.register_blueprint(equipamentos_bp)
    app.register_blueprint(dashboard_bp)

    @app.errorhandler(404)
    def nao_encontrado(_erro):
        return render_template("erro.html", codigo=404,
                               titulo="Página não encontrada",
                               mensagem="O link acessado não existe ou foi movido."), 404

    @app.errorhandler(500)
    def erro_interno(_erro):
        return render_template("erro.html", codigo=500,
                               titulo="Algo deu errado",
                               mensagem="Ocorreu um erro inesperado. Tente novamente em alguns instantes."), 500

    @app.after_request
    def aplicar_headers_seguranca(resposta):
        resposta.headers["X-Content-Type-Options"] = "nosniff"
        resposta.headers["X-Frame-Options"] = "SAMEORIGIN"
        resposta.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        resposta.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains"
        return resposta

    return app


# Top-level instance required by Vercel's Python runtime
app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
