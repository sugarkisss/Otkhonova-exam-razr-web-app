# models.py
# Файл с моделями данных. Создан мной для описания таблиц через SQLAlchemy.
# Здесь настроены все связи и каскадные удаления (ON DELETE CASCADE) по ТЗ.

from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

# Инициализируем объект базы данных
db = SQLAlchemy()

# Таблица-связка для связи «многие ко многим» между Книгами и Жанрами по ТЗ
books_genres = db.Table('books_genres',
    db.Column('book_id', db.Integer, db.ForeignKey('books.id', ondelete='CASCADE'), primary_key=True),
    db.Column('genre_id', db.Integer, db.ForeignKey('genres.id', ondelete='CASCADE'), primary_key=True)
)

class Role(db.Model):
    """ Роли пользователей в системе """
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)
    description = db.Column(db.Text, nullable=False)

class User(db.Model, UserMixin):
    """ Таблица учетных записей пользователей """
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    login = db.Column(db.String(50), nullable=False, unique=True)
    password_hash = db.Column(db.String(255), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    first_name = db.Column(db.String(50), nullable=False)
    middle_name = db.Column(db.String(50), nullable=True) # По ТЗ отчество может отсутствовать
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'), nullable=False)
    
    role = db.relationship('Role', backref='users')

class Genre(db.Model):
    """ Таблица доступных литературных жанров """
    __tablename__ = 'genres'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)

class Book(db.Model):
    """ Основная таблица книг """
    __tablename__ = 'books'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=False) # Текст в формате Markdown
    year = db.Column(db.Integer, nullable=False)
    publisher = db.Column(db.String(255), nullable=False)
    author = db.Column(db.String(255), nullable=False)
    pages = db.Column(db.Integer, nullable=False)

    genres = db.relationship('Genre', secondary=books_genres, backref=db.backref('books', lazy='dynamic'))

class Cover(db.Model):
    """ Таблица метаданных обложек книг """
    __tablename__ = 'covers'
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    mime_type = db.Column(db.String(100), nullable=False)
    md5_hash = db.Column(db.String(32), nullable=False) # Хэш для дедупликации картинок
    book_id = db.Column(db.Integer, db.ForeignKey('books.id', ondelete='CASCADE'), nullable=False)
    
    # ТЗ: Каскадное удаление записи при удалении книги
    book = db.relationship('Book', backref=db.backref('cover', uselist=False, cascade='all, delete-orphan'))

class ReviewStatus(db.Model):
    """ Вариант 1: Справочник статусов проверки отзывов модератором """
    __tablename__ = 'review_statuses'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)

class Review(db.Model):
    """ Таблица пользовательских рецензий """
    __tablename__ = 'reviews'
    id = db.Column(db.Integer, primary_key=True)
    book_id = db.Column(db.Integer, db.ForeignKey('books.id', ondelete='CASCADE'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    text = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow) # Автодата по ТЗ
    status_id = db.Column(db.Integer, db.ForeignKey('review_statuses.id'), nullable=False, default=1)

    book = db.relationship('Book', backref=db.backref('reviews', cascade='all, delete-orphan'))
    user = db.relationship('User', backref='reviews')
    status = db.relationship('ReviewStatus', backref='reviews')