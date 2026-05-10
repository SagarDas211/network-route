from app import create_app
from app.extensions import db

app = create_app()

if __name__ == "__main__":
    if app.config["AUTO_CREATE_TABLES"]:
        with app.app_context():
            db.create_all()

    app.run(host="0.0.0.0", port=5000, debug=True, use_reloader=False)
