from flask import Flask

from config import SECRET_KEY
from database.db import init_db
from routes.history_routes import history_bp
from routes.invoice_routes import invoice_bp
from routes.product_routes import product_bp


def create_app() -> Flask:
    app = Flask(__name__)
    app.config["SECRET_KEY"] = SECRET_KEY
    init_db()
    app.register_blueprint(invoice_bp)
    app.register_blueprint(history_bp)
    app.register_blueprint(product_bp)
    return app


app = create_app()


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
