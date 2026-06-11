# models.py
# Здесь я описываю, как выглядят таблицы в базе данных.


from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()

# --- Вспомогательная таблица для связи "многие ко многим" между книгами и жанрами ---
# Книга может иметь много жанров, жанр может быть у многих книг.
books_genres = db.Table('books_genres',
    db.Column('book_id', db.Integer, db.ForeignKey('books.id', ondelete='CASCADE'), primary_key=True),
    db.Column('genre_id', db.Integer, db.ForeignKey('genres.id', ondelete='CASCADE'), primary_key=True)
)

# Роли пользователей (Администратор, Модератор, Пользователь)
class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)
    description = db.Column(db.Text, nullable=False)   # текстовое описание роли

# Пользователи — наследуем UserMixin, чтобы Flask-Login работал (is_authenticated и т.д.)
class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    login = db.Column(db.String(50), nullable=False, unique=True)   # уникальный логин
    password_hash = db.Column(db.String(255), nullable=False)      # пока храним как строку (для экзамена)
    last_name = db.Column(db.String(50), nullable=False)
    first_name = db.Column(db.String(50), nullable=False)
    middle_name = db.Column(db.String(50), nullable=True)          # отчество не обязательно
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'), nullable=False)

    # Связь: у роли может быть много пользователей
    role = db.relationship('Role', backref='users')

# Жанры книг
class Genre(db.Model):
    __tablename__ = 'genres'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)   # например, "Фантастика"

# Книги — центральная сущность
class Book(db.Model):
    __tablename__ = 'books'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)              # название
    description = db.Column(db.Text, nullable=False)               # аннотация (поддерживает Markdown)
    year = db.Column(db.Integer, nullable=False)                   # год издания
    publisher = db.Column(db.String(255), nullable=False)          # издательство
    author = db.Column(db.String(255), nullable=False)             # автор
    pages = db.Column(db.Integer, nullable=False)                  # количество страниц

    # Связь с жанрами через таблицу books_genres
    genres = db.relationship('Genre', secondary=books_genres,
                             backref=db.backref('books', lazy='dynamic'))

# Обложки книг (вынесены в отдельную таблицу для дедупликации по MD5)
class Cover(db.Model):
    __tablename__ = 'covers'
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)           # имя файла на диске
    mime_type = db.Column(db.String(100), nullable=False)          # тип картинки (image/jpeg и т.п.)
    md5_hash = db.Column(db.String(32), nullable=False)            # хэш содержимого
    book_id = db.Column(db.Integer, db.ForeignKey('books.id', ondelete='CASCADE'), nullable=False)

    # Обратная связь: у книги может быть одна обложка (uselist=False)
    book = db.relationship('Book', backref=db.backref('cover', uselist=False, cascade='all, delete-orphan'))

# Статусы рецензий (Вариант 1: На рассмотрении, Одобрена, Отклонена)
class ReviewStatus(db.Model):
    __tablename__ = 'review_statuses'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)

# Рецензии пользователей
class Review(db.Model):
    __tablename__ = 'reviews'
    id = db.Column(db.Integer, primary_key=True)
    book_id = db.Column(db.Integer, db.ForeignKey('books.id', ondelete='CASCADE'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)                 # оценка от 1 до 5
    text = db.Column(db.Text, nullable=False)                      # текст рецензии
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)   # дата создания (автоматически)
    status_id = db.Column(db.Integer, db.ForeignKey('review_statuses.id'), nullable=False, default=1)

    # Связи для удобной навигации
    book = db.relationship('Book', backref=db.backref('reviews', cascade='all, delete-orphan'))
    user = db.relationship('User', backref='reviews')
    status = db.relationship('ReviewStatus', backref='reviews')