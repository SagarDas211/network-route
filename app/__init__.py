import os

from flask import Flask, jsonify
from dotenv import load_dotenv

from app.extensions import db
from app.routes import api


def create_app(test_config=None):
    load_dotenv()

    app = Flask(__name__)

    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:postgres@localhost:5432/network_route",
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["AUTO_CREATE_TABLES"] = os.getenv("AUTO_CREATE_TABLES", "true").lower() == "true"

    if test_config:
        app.config.update(test_config)

    db.init_app(app)
    app.register_blueprint(api)

    @app.get("/health")
    def health_check():
        return jsonify({"status": "ok"})

    return app
