from app import app, db
from models import Book, User, Role, Genre, Cover, Review, ReviewStatus

with app.app_context():
    db.create_all()
    print('Таблицы созданы!')
