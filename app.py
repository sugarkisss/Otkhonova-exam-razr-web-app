# app.py
# (Вариант 1)
# Автор: Отхонова Амуланга Александровна, группа 241-371


import os
import hashlib               # хэш для картинок, чтобы не хранить дубликаты
import bleach                # чистит HTML от опасных скриптов (XSS защита)
from flask import Flask, render_template, redirect, url_for, flash, request, abort
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash, generate_password_hash  # хеши паролей (в моём коде пока не используется, но импорт оставила на будущее)
from werkzeug.utils import secure_filename   # приводит имя файла к безопасному виду

# Модели данных — вынесла в отдельный файл, чтобы не загромождать логику
from models import db, User, Role, Book, Genre, Cover, Review, ReviewStatus

app = Flask(__name__)

# --- Настройки конфигурации  ---
app.config['SECRET_KEY'] = '2213gkwldngs56'   
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(BASE_DIR, 'instance', 'library.db')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + db_path   # база SQLite, файл создаётся сам

app.config['UPLOAD_FOLDER'] = os.path.join(BASE_DIR, 'static', 'covers')  # сюда сохраняются обложки

# Подключаем БД к приложению
db.init_app(app)

# --- Настройка логина (Flask-Login) ---
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'   # если не авторизован — кидаем на страницу входа
login_manager.login_message = "Для выполнения данного действия необходимо пройти процедуру аутентификации"
login_manager.login_message_category = "warning"

@login_manager.user_loader
def load_user(user_id):
    # Flask-Login вызывает эту функцию, чтобы получить объект пользователя по id
    return User.query.get(int(user_id))

# --- Декоратор для проверки ролей  ---
def check_role(role_names):
    """ Проверяет, есть ли у текущего пользователя одна из разрешённых ролей.
        Если нет — показывает ошибку и отправляет на главную. """
    def decorator(f):
        def wrapped(*args, **kwargs):
            if not current_user.is_authenticated or current_user.role.name not in role_names:
                flash("У вас недостаточно прав для выполнения данного действия", "danger")
                return redirect(url_for('index'))
            return f(*args, **kwargs)
        wrapped.__name__ = f.__name__
        return wrapped
    return decorator

# --- МАРШРУТЫ (то, что видит пользователь) ---

# 1. Главная страница — список книг с пагинацией
@app.route('/')
def index():
    page = request.args.get('page', 1, type=int)   # текущая страница (по умолчанию 1)
    # Сортировка по убыванию id — сначала новые книги, per_page=10 как сказано в задании
    pagination = Book.query.order_by(Book.id.desc()).paginate(page=page, per_page=10, error_out=False)
    books = pagination.items

    # Считаем средний рейтинг и количество рецензий ТОЛЬКО для одобренных (status_id=2)
    for book in books:
        approved_reviews = [r for r in book.reviews if r.status_id == 2]
        book.reviews_count = len(approved_reviews)
        if book.reviews_count > 0:
            book.avg_rating = round(sum(r.rating for r in approved_reviews) / book.reviews_count, 1)
        else:
            book.avg_rating = "Нет оценок"

    return render_template('index.html', books=books, pagination=pagination)

# 2. Вход в систему
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        login_val = request.form.get('login')
        password_val = request.form.get('password')
        remember = True if request.form.get('remember') else False

        user = User.query.filter_by(login=login_val).first()

        
        if user and user.password_hash == password_val:
            login_user(user, remember=remember)
            return redirect(url_for('index'))

        flash("Невозможно аутентифицироваться с указанными логином и паролем", "danger")
    return render_template('login.html')

# 3. Выход
@app.route('/logout')
@login_required       # без логина сюда нельзя попасть
def logout():
    logout_user()
    return redirect(url_for('index'))

# 4. Карточка книги — подробный просмотр
@app.route('/book/<int:book_id>')
def book_view(book_id):
    book = Book.query.get_or_404(book_id)   # если книги нет — 404 ошибка
    # Показываем только одобренные рецензии (Вариант 1)
    approved_reviews = Review.query.filter_by(book_id=book_id, status_id=2).all()

    # Проверяем, писал ли текущий пользователь рецензию на эту книгу (чтобы скрыть кнопку "Написать")
    user_review = None
    if current_user.is_authenticated:
        user_review = Review.query.filter_by(book_id=book_id, user_id=current_user.id).first()

    return render_template('book_view.html', book=book, reviews=approved_reviews, user_review=user_review)

# 5. Добавление книги — доступно только администратору
@app.route('/book/add', methods=['GET', 'POST'])
@login_required
@check_role(['Администратор'])
def book_add():
    genres = Genre.query.all()   # все жанры для выпадающего списка
    if request.method == 'POST':
        try:
            title = request.form.get('title')
            description = request.form.get('description')
            year = int(request.form.get('year'))
            publisher = request.form.get('publisher')
            author = request.form.get('author')
            pages = int(request.form.get('pages'))
            selected_genres = request.form.getlist('genres')

            # Чистим описание через bleach — чтобы нельзя было вставить <script> и т.п.
            clean_description = bleach.clean(description, tags=['p', 'b', 'i', 'strong', 'em', 'ul', 'ol', 'li'])

            # Обложка
            file = request.files.get('cover')
            if not file or file.filename == '':
                flash("Необходимо загрузить файл обложки", "danger")
                return render_template('book_form.html', genres=genres, is_edit=False)

            # Считаем MD5 содержимого файла, чтобы не хранить две одинаковые картинки
            file_bytes = file.read()
            file_hash = hashlib.md5(file_bytes).hexdigest()
            file.seek(0)   # возвращаем указатель в начало

            # Создаём книгу, но пока не коммитим
            new_book = Book(title=title, description=clean_description, year=year,
                            publisher=publisher, author=author, pages=pages)
            for g_id in selected_genres:
                genre = Genre.query.get(int(g_id))
                if genre:
                    new_book.genres.append(genre)

            db.session.add(new_book)
            db.session.flush()   # чтобы получить new_book.id до коммита

            # Проверяем, есть ли уже файл с таким же хэшем
            existing_cover = Cover.query.filter_by(md5_hash=file_hash).first()
            if existing_cover:
                # Переиспользуем старую картинку
                new_cover = Cover(filename=existing_cover.filename, mime_type=file.content_type,
                                  md5_hash=file_hash, book_id=new_book.id)
            else:
                ext = os.path.splitext(secure_filename(file.filename))[1]
                filename = f"{file_hash}{ext}"

                # Создаём папку для обложек, если её нет (на OneDrive иногда глючит)
                if not os.path.exists(app.config['UPLOAD_FOLDER']):
                    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

                # Сохраняем файл вручную, потому что file.save() на некоторых машинах падал
                target_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                with open(target_path, 'wb') as f_target:
                    f_target.write(file_bytes)

                new_cover = Cover(filename=filename, mime_type=file.content_type,
                                  md5_hash=file_hash, book_id=new_book.id)

            db.session.add(new_cover)
            db.session.commit()   # всё вместе сохраняем в БД

            flash("Книга успешно добавлена!", "success")
            return redirect(url_for('book_view', book_id=new_book.id))

        except Exception as e:
            db.session.rollback()   # если что-то пошло не так — откатываем
            print("!!! ОШИБКА ПРИ ДОБАВЛЕНИИ КНИГИ !!!")
            print(e)
            flash(f"Ошибка сохранения: {e}", "danger")

    return render_template('book_form.html', genres=genres, is_edit=False)

# 6. Редактирование книги — доступно админу и модератору
@app.route('/book/<int:book_id>/edit', methods=['GET', 'POST'])
@login_required
@check_role(['Администратор', 'Модератор'])
def book_edit(book_id):
    book = Book.query.get_or_404(book_id)
    genres = Genre.query.all()
    if request.method == 'POST':
        try:
            # Обновляем все поля
            book.title = request.form.get('title')
            book.year = int(request.form.get('year'))
            book.publisher = request.form.get('publisher')
            book.author = request.form.get('author')
            book.pages = int(request.form.get('pages'))
            book.description = bleach.clean(request.form.get('description'), tags=['p', 'b', 'i', 'strong', 'em', 'ul', 'ol', 'li'])

            # Обновляем жанры (очищаем и добавляем заново)
            book.genres = []
            for g_id in request.form.getlist('genres'):
                genre = Genre.query.get(int(g_id))
                if genre:
                    book.genres.append(genre)

            db.session.commit()
            flash("Книга успешно отредактирована!", "success")
            return redirect(url_for('book_view', book_id=book.id))
        except Exception as e:
            db.session.rollback()
            flash(f"Ошибка editing: {e}", "danger")

    return render_template('book_form.html', book=book, genres=genres, is_edit=True)

# 7. Удаление книги — только админ
@app.route('/book/<int:book_id>/delete', methods=['POST'])
@login_required
@check_role(['Администратор'])
def book_delete(book_id):
    book = Book.query.get_or_404(book_id)
    try:
        cover = book.cover
        if cover:
            # Если эту картинку больше никто не использует — удаляем файл с диска
            same_covers = Cover.query.filter_by(filename=cover.filename).all()
            if len(same_covers) <= 1:
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], cover.filename)
                if os.path.exists(file_path):
                    os.remove(file_path)

        db.session.delete(book)   # каскадно удалятся обложка и рецензии
        db.session.commit()
        flash("Книга и все связанные с ней данные успешно удалены!", "success")
    except Exception:
        db.session.rollback()
        flash("Ошибка при удалении книги.", "danger")

    return redirect(url_for('index'))

# 8. Написание рецензии (только авторизованный пользователь)
@app.route('/book/<int:book_id>/review', methods=['GET', 'POST'])
@login_required
def review_add(book_id):
    book = Book.query.get_or_404(book_id)

    # Нельзя написать вторую рецензию на ту же книгу
    existing = Review.query.filter_by(book_id=book_id, user_id=current_user.id).first()
    if existing:
        flash("Вы уже оставили рецензию на эту книгу", "warning")
        return redirect(url_for('book_view', book_id=book_id))

    if request.method == 'POST':
        rating = int(request.form.get('rating'))
        text = request.form.get('text')
        clean_text = bleach.clean(text, tags=['p', 'b', 'i', 'strong', 'em', 'ul', 'ol', 'li'])

        # Новый отзыв получает статус 1 = "На рассмотрении" (Вариант 1)
        new_review = Review(book_id=book_id, user_id=current_user.id,
                            rating=rating, text=clean_text, status_id=1)
        db.session.add(new_review)
        db.session.commit()

        flash("Рецензия успешно отправлена на модерацию!", "success")
        return redirect(url_for('book_view', book_id=book_id))

    return render_template('review.html', book=book)

# --- РОУТЫ ПО ИНДИВИДУАЛЬНОМУ ВАРИАНТУ 1 ---

# Мои рецензии (для пользователя)
@app.route('/my-reviews')
@login_required
@check_role(['Пользователь'])
def user_reviews():
    reviews = Review.query.filter_by(user_id=current_user.id).order_by(Review.created_at.desc()).all()
    return render_template('user_reviews.html', reviews=reviews)

# Список рецензий на модерации (для модератора)
@app.route('/moderation')
@login_required
@check_role(['Модератор'])
def moderation_list():
    page = request.args.get('page', 1, type=int)
    pagination = Review.query.filter_by(status_id=1).order_by(Review.created_at.asc()).paginate(page=page, per_page=10, error_out=False)
    reviews = pagination.items
    return render_template('moderation.html', reviews=reviews, pagination=pagination)

# Страница просмотра и одобрения/отклонения конкретной рецензии
@app.route('/moderation/<int:review_id>', methods=['GET', 'POST'])
@login_required
@check_role(['Модератор'])
def review_view(review_id):
    review = Review.query.get_or_404(review_id)
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'approve':
            review.status_id = 2   # Одобрена
            flash("Рецензия успешно одобрена и опубликована!", "success")
        elif action == 'reject':
            review.status_id = 3   # Отклонена
            flash("Рецензия успешно отклонена!", "warning")
        db.session.commit()
        return redirect(url_for('moderation_list'))
    return render_template('review_view.html', review=review)

# Удаление рецензии (автор, модератор или админ)
@app.route('/delete_review/<int:review_id>', methods=['POST'])
@login_required
def delete_review(review_id):
    review = Review.query.get_or_404(review_id)

    is_admin_or_mod = current_user.role.name in ['Администратор', 'Модератор']

    if current_user.id == review.user_id or is_admin_or_mod:
        db.session.delete(review)
        db.session.commit()
        flash('Рецензия успешно удалена!', 'success')
    else:
        flash('У вас нет прав для удаления этой рецензии.', 'danger')

    return redirect(url_for('book_view', book_id=review.book_id))

# --- Заполнение базы данных начальными значениями (срабатывает при первом запуске) ---
if __name__ == '__main__':
    with app.app_context():
        db.create_all()   # создаёт таблицы, если их нет

        # Роли
        if not Role.query.first():
            db.session.add_all([
                Role(id=1, name='Администратор', description='Полный доступ к системе'),
                Role(id=2, name='Модератор', description='Модерация рецензий и правка книг'),
                Role(id=3, name='Пользователь', description='Обычный читатель, пишет отзывы')
            ])
            db.session.commit()

        # Статусы рецензий
        if not ReviewStatus.query.first():
            db.session.add_all([
                ReviewStatus(id=1, name='На рассмотрении'),
                ReviewStatus(id=2, name='Одобрена'),
                ReviewStatus(id=3, name='Отклонена')
            ])
            db.session.commit()

        # Жанры (по умолчанию)
        if not Genre.query.first():
            db.session.add_all([
                Genre(name='Фантастика'), Genre(name='Детектив'),
                Genre(name='Роман'), Genre(name='Техническая литература')
            ])
            db.session.commit()

        # Тестовые пользователи (чтобы было с кем входить)
        if not User.query.filter_by(login='admin').first():
            db.session.add(User(login='admin', password_hash='admin', last_name='Петров', first_name='Алексей', role_id=1))
        if not User.query.filter_by(login='moderator').first():
            db.session.add(User(login='moderator', password_hash='mod', last_name='Сидоров', first_name='Николай', role_id=2))
        if not User.query.filter_by(login='user').first():
            db.session.add(User(login='user', password_hash='user', last_name='Иванова', first_name='Мария', role_id=3))

        db.session.commit()

    app.run(debug=True)   # debug=True — чтобы не перезапускать вручную при изменениях