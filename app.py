# app.py
# Главный файл веб-приложения Flask. Написан мной для сдачи экзамена.
# Содержит роуты, авторизацию, логику загрузки файлов, обработку ошибок баз данных.

import os
import hashlib
import bleach  # Все импорты вынесены наверх по стандарту PEP 8
from flask import Flask, render_template, redirect, url_for, flash, request, abort
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename

# Импортируем созданную базу и модели из соседнего файла
from models import db, User, Role, Book, Genre, Cover, Review, ReviewStatus

app = Flask(__name__)

# --- НАСТРОЙКИ КОНФИГУРАЦИИ ---
app.config['SECRET_KEY'] = 'mospoly_super_secret_2026'
# Подключаем легкую базу SQLite, файл создастся сам прямо в папке проекта
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(BASE_DIR, 'instance', 'library.db')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + db_path

app.config['UPLOAD_FOLDER'] = os.path.join(BASE_DIR, 'static', 'covers')

# Инициализируем БД
db.init_app(app)

# Настраиваем менеджер авторизации Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login' 
login_manager.login_message = "Для выполнения данного действия необходимо пройти процедуру аутентификации"
login_manager.login_message_category = "warning"

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --- ДЕКОРАТОР ДЛЯ ПРОВЕРКИ РОЛЕЙ И ПРАВ ДОСТУПА ---
def check_role(role_names):
    """ Кастомный декоратор для разграничения прав.
        Если прав не хватает — кидает на главную с flash-уведомлением по ТЗ. """
    def decorator(f):
        def wrapped(*args, **kwargs):
            if not current_user.is_authenticated or current_user.role.name not in role_names:
                flash("У вас недостаточно прав для выполнения данного действия", "danger")
                return redirect(url_for('index'))
            return f(*args, **kwargs)
        wrapped.__name__ = f.__name__
        return wrapped
    return decorator


# --- МАРШРУТЫ ПРИЛОЖЕНИЯ (РОУТЫ) ---

# 1. Главная страница (Вывод списка книг с пагинацией)
@app.route('/')
def index():
    page = request.args.get('page', 1, type=int)
    # Сортируем по убыванию id (сначала новые) и выводим строго по 10 штук по ТЗ
    pagination = Book.query.order_by(Book.id.desc()).paginate(page=page, per_page=10, error_out=False)
    books = pagination.items
    
    # Считаем среднюю оценку и кол-во отзывов для каждой книги (только ОДОБРЕННЫХ по Варианту 1)
    for book in books:
        approved_reviews = [r for r in book.reviews if r.status_id == 2]
        book.reviews_count = len(approved_reviews)
        if book.reviews_count > 0:
            book.avg_rating = round(sum(r.rating for r in approved_reviews) / book.reviews_count, 1)
        else:
            book.avg_rating = "Нет оценок"
            
    return render_template('index.html', books=books, pagination=pagination)

# 2. Аутентификация (Страница входа)
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        login_val = request.form.get('login')
        password_val = request.form.get('password')
        remember = True if request.form.get('remember') else False
        
        user = User.query.filter_by(login=login_val).first()
        
        # Простая проверка пароля для демонстрации на экзамене
        if user and user.password_hash == password_val:
            login_user(user, remember=remember)
            return redirect(url_for('index'))
            
        flash("Невозможно аутентифицироваться с указанными логином и паролем", "danger")
    return render_template('login.html')

# 3. Выход из аккаунта
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

# 4. Просмотр конкретной книги
@app.route('/book/<int:book_id>')
def book_view(book_id):
    book = Book.query.get_or_404(book_id)
    # Показываем только одобренные модератором отзывы (Вариант 1)
    approved_reviews = Review.query.filter_by(book_id=book_id, status_id=2).all()
    
    # Ищем, писал ли уже этот пользователь отзыв, чтобы скрыть/показать кнопку по ТЗ
    user_review = None
    if current_user.is_authenticated:
        user_review = Review.query.filter_by(book_id=book_id, user_id=current_user.id).first()
        
    return render_template('book_view.html', book=book, reviews=approved_reviews, user_review=user_review)

# 5. Добавление книги (Только Администратор)
@app.route('/book/add', methods=['GET', 'POST'])
@login_required
@check_role(['Администратор'])
def book_add():
    genres = Genre.query.all()
    if request.method == 'POST':
        try:
            title = request.form.get('title')
            description = request.form.get('description')
            year = int(request.form.get('year'))
            publisher = request.form.get('publisher')
            author = request.form.get('author')
            pages = int(request.form.get('pages'))
            selected_genres = request.form.getlist('genres')
            
            # Санитария данных через Bleach для защиты от XSS-скриптов
            clean_description = bleach.clean(description, tags=['p', 'b', 'i', 'strong', 'em', 'ul', 'ol', 'li'])
            
            # Обработка файла обложки
            file = request.files.get('cover')
            if not file or file.filename == '':
                flash("Необходимо загрузить файл обложки", "danger")
                return render_template('book_form.html', genres=genres, is_edit=False)
                
            # Вычисляем MD5-хэш файла для предотвращения дублирования картинок на сервере (по ТЗ)
            file_bytes = file.read()
            file_hash = hashlib.md5(file_bytes).hexdigest()
            file.seek(0)
            
            new_book = Book(title=title, description=clean_description, year=year, publisher=publisher, author=author, pages=pages)
            for g_id in selected_genres:
                genre = Genre.query.get(int(g_id))
                if genre:
                    new_book.genres.append(genre)
            
            db.session.add(new_book)
            db.session.flush() # Получаем ID новой книги до фиксации транзакции
            
            # Проверяем, загружался ли файл с таким хэшем ранее
            existing_cover = Cover.query.filter_by(md5_hash=file_hash).first()
            if existing_cover:
                new_cover = Cover(filename=existing_cover.filename, mime_type=file.content_type, md5_hash=file_hash, book_id=new_book.id)
            else:
                ext = os.path.splitext(secure_filename(file.filename))[1]
                filename = f"{file_hash}{ext}"
                
                # БЕЗОПАСНАЯ ПРОВЕРКА ДЛЯ ONEDRIVE: проверяем и создаем папку, если её нет
                if not os.path.exists(app.config['UPLOAD_FOLDER']):
                    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
                    
                # ХИТРЫЙ ОБХОД БЛОКИРОВОК: пишем байты картинки напрямую, минуя стандартный file.save()
                target_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                with open(target_path, 'wb') as f_target:
                    f_target.write(file_bytes)
                
                new_cover = Cover(filename=filename, mime_type=file.content_type, md5_hash=file_hash, book_id=new_book.id)
                
            db.session.add(new_cover)
            db.session.commit()
            
            flash("Книга успешно добавлена!", "success")
            return redirect(url_for('book_view', book_id=new_book.id))
            
        except Exception as e:
            db.session.rollback() # Откат транзакции при ошибках БД по ТЗ
            print("!!! ОШИБКА ПРИ ДОБАВЛЕНИИ КНИГИ !!!")
            print(e)
            flash(f"Ошибка сохранения: {e}", "danger")
            
    return render_template('book_form.html', genres=genres, is_edit=False)

# 6. Редактирование книги (Администратор и Модератор)
@app.route('/book/<int:book_id>/edit', methods=['GET', 'POST'])
@login_required
@check_role(['Администратор', 'Модератор'])
def book_edit(book_id):
    book = Book.query.get_or_404(book_id)
    genres = Genre.query.all()
    if request.method == 'POST':
        try:
            book.title = request.form.get('title')
            book.year = int(request.form.get('year'))
            book.publisher = request.form.get('publisher')
            book.author = request.form.get('author')
            book.pages = int(request.form.get('pages'))
            book.description = bleach.clean(request.form.get('description'), tags=['p', 'b', 'i', 'strong', 'em', 'ul', 'ol', 'li'])
            
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

# 7. Удаление книги (Только Администратор)
@app.route('/book/<int:book_id>/delete', methods=['POST'])
@login_required
@check_role(['Администратор'])
def book_delete(book_id):
    book = Book.query.get_or_404(book_id)
    try:
        cover = book.cover
        if cover:
            # Если файл картинки больше не привязан к другим книгам, удаляем его с диска
            same_covers = Cover.query.filter_by(filename=cover.filename).all()
            if len(same_covers) <= 1:
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], cover.filename)
                if os.path.exists(file_path):
                    os.remove(file_path)
                    
        db.session.delete(book)
        db.session.commit()
        flash("Книга и все связанные с ней данные успешно удалены!", "success")
    except Exception:
        db.session.rollback()
        flash("Ошибка при удалении книги.", "danger")
        
    return redirect(url_for('index'))

# 8. Написание рецензии
@app.route('/book/<int:book_id>/review', methods=['GET', 'POST'])
@login_required
def review_add(book_id):
    book = Book.query.get_or_404(book_id)
    
    existing = Review.query.filter_by(book_id=book_id, user_id=current_user.id).first()
    if existing:
        flash("Вы уже оставили рецензию на эту книгу", "warning")
        return redirect(url_for('book_view', book_id=book_id))
        
    if request.method == 'POST':
        rating = int(request.form.get('rating'))
        text = request.form.get('text')
        
        clean_text = bleach.clean(text, tags=['p', 'b', 'i', 'strong', 'em', 'ul', 'ol', 'li'])
        
        # Новая рецензия падает со статусом 1 ("На рассмотрении") по Варианту 1
        new_review = Review(book_id=book_id, user_id=current_user.id, rating=rating, text=clean_text, status_id=1)
        db.session.add(new_review)
        db.session.commit()
        
        flash("Рецензия успешно отправлена на модерацию!", "success")
        return redirect(url_for('book_view', book_id=book_id))
        
    return render_template('review.html', book=book)


# --- РОУТЫ ИНДИВИДУАЛЬНОГО ВАРИАНТА 1 ---

@app.route('/my-reviews')
@login_required
@check_role(['Пользователь'])
def user_reviews():
    reviews = Review.query.filter_by(user_id=current_user.id).order_by(Review.created_at.desc()).all()
    return render_template('user_reviews.html', reviews=reviews)

@app.route('/moderation')
@login_required
@check_role(['Модератор'])
def moderation_list():
    page = request.args.get('page', 1, type=int)
    pagination = Review.query.filter_by(status_id=1).order_by(Review.created_at.asc()).paginate(page=page, per_page=10, error_out=False)
    reviews = pagination.items
    return render_template('moderation.html', reviews=reviews, pagination=pagination)

@app.route('/moderation/<int:review_id>', methods=['GET', 'POST'])
@login_required
@check_role(['Модератор'])
def review_view(review_id):
    review = Review.query.get_or_404(review_id)
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'approve':
            review.status_id = 2 # Одобрена
            flash("Рецензия успешно одобрена и опубликована!", "success")
        elif action == 'reject':
            review.status_id = 3 # Отклонена
            flash("Рецензия успешно отклонена!", "warning")
        db.session.commit()
        return redirect(url_for('moderation_list'))
        
    return render_template('review_view.html', review=review)


# --- АВТОНАПОЛНЕНИЕ БАЗЫ SQLite ПРИ ПЕРВОМ СТАРТЕ ---
if __name__ == '__main__':
    with app.app_context():
        db.create_all() 
        
        if not Role.query.first():
            db.session.add_all([
                Role(id=1, name='Администратор', description='Полный доступ к системе'),
                Role(id=2, name='Модератор', description='Модерация рецензий и правка книг'),
                Role(id=3, name='Пользователь', description='Обычный читатель, пишет отзывы')
            ])
            db.session.commit()
            
        if not ReviewStatus.query.first():
            db.session.add_all([
                ReviewStatus(id=1, name='На рассмотрении'),
                ReviewStatus(id=2, name='Одобрена'),
                ReviewStatus(id=3, name='Отклонена')
            ])
            db.session.commit()

        if not Genre.query.first():
            db.session.add_all([
                Genre(name='Фантастика'), Genre(name='Детектив'), 
                Genre(name='Роман'), Genre(name='Техническая литература')
            ])
            db.session.commit()

        # Тестовые юзеры для демонстрации защиты
        if not User.query.filter_by(login='admin').first():
            db.session.add(User(login='admin', password_hash='admin', last_name='Петров', first_name='Алексей', role_id=1))
        if not User.query.filter_by(login='moderator').first():
            db.session.add(User(login='moderator', password_hash='mod', last_name='Сидоров', first_name='Николай', role_id=2))
        if not User.query.filter_by(login='user').first():
            db.session.add(User(login='user', password_hash='user', last_name='Иванова', first_name='Мария', role_id=3))
            
        db.session.commit()

    app.run(debug=True)