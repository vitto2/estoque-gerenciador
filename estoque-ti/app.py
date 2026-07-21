import os

from flask import Flask, redirect, url_for

from config import Config, INSTANCE_DIR
from models import db


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    os.makedirs(INSTANCE_DIR, exist_ok=True)

    db.init_app(app)

    with app.app_context():
        db.create_all()

    from routes.dashboard import dashboard_bp
    from routes.equipamentos import equipamentos_bp

    app.register_blueprint(equipamentos_bp)
    app.register_blueprint(dashboard_bp)

    @app.route("/")
    def index():
        return redirect(url_for("equipamentos.listagem"))

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
