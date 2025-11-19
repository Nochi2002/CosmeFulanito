from app import create_app
from app.models import db
import os

app = create_app()

print(f"--> BASE DE DATOS EN: {app.config['SQLALCHEMY_DATABASE_URI']}")

with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run(debug=True, port=5000)