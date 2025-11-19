from app import create_app
from app.models import db

# Franco no te olvides de comentar los procesos, modelos o lo que agregues
# nos va a servir para cuando estemos defendiendo, capaz q te olvidas como lo hiciste por los nervios nashe
app = create_app()

with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run(debug=True, port=5000)