-- Скрипт инициализации базы данных «Электронная библиотека»

-- 1. Создание таблицы ролей пользователей
CREATE TABLE IF NOT EXISTS roles (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE,
    description TEXT NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 2. Создание таблицы пользователей
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    login VARCHAR(50) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    first_name VARCHAR(50) NOT NULL,
    middle_name VARCHAR(50) NULL, -- Единственное необязательное поле
    role_id INT NOT NULL,
    FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 3. Создание таблицы книг
CREATE TABLE IF NOT EXISTS books (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    year INT NOT NULL, -- В SQLAlchemy укажем тип Year, в MySQL используем INT/YEAR
    publisher VARCHAR(255) NOT NULL,
    author VARCHAR(255) NOT NULL,
    pages INT NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 4. Создание таблицы жанров
CREATE TABLE IF NOT EXISTS genres (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 5. Соединительная таблица Книги-Жанры (Связь многие-ко-многим)
-- ON DELETE CASCADE обязателен по ТЗ: если книга удаляется, удаляются и связи с жанрами
CREATE TABLE IF NOT EXISTS books_genres (
    book_id INT NOT NULL,
    genre_id INT NOT NULL,
    PRIMARY KEY (book_id, genre_id),
    FOREIGN KEY (book_id) REFERENCES books(id) ON DELETE CASCADE,
    FOREIGN KEY (genre_id) REFERENCES genres(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 6. Создание таблицы обложек книг (Связь один-к-одному/многие-к-одному)
-- ON DELETE CASCADE: удаление книги автоматически удалит запись об обложке в БД
CREATE TABLE IF NOT EXISTS covers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    filename VARCHAR(255) NOT NULL,
    mime_type VARCHAR(100) NOT NULL,
    md5_hash VARCHAR(32) NOT NULL,
    book_id INT NOT NULL,
    FOREIGN KEY (book_id) REFERENCES books(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 7. ВАРИАНТ 1: Таблица статусов рецензий
CREATE TABLE IF NOT EXISTS review_statuses (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 8. Создание таблицы рецензий
-- ON DELETE CASCADE: при удалении книги или пользователя удаляются их рецензии
CREATE TABLE IF NOT EXISTS reviews (
    id INT AUTO_INCREMENT PRIMARY KEY,
    book_id INT NOT NULL,
    user_id INT NOT NULL,
    rating INT NOT NULL, -- Оценка числом от 0 до 5
    text TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, -- Автозаполнение времени
    status_id INT NOT NULL, -- Поле из Варианта 1
    FOREIGN KEY (book_id) REFERENCES books(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (status_id) REFERENCES review_statuses(id) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;


-- ЗАПОЛНЕНИЕ ПЕРВОНАЧАЛЬНЫХ ДАННЫХ (Заполняются в СУБД, админка не нужна)

-- Накатываем роли по заданию
INSERT INTO roles (id, name, description) VALUES
(1, 'Администратор', 'Полный доступ к системе, создание и удаление книг'),
(2, 'Модератор', 'Редактирование данных книг и модерация рецензий'),
(3, 'Пользователь', 'Просмотр книг и написание рецензий')
ON DUPLICATE KEY UPDATE name=name;

-- Накатываем статусы рецензий (Вариант 1)
INSERT INTO review_statuses (id, name) VALUES
(1, 'На рассмотрении'),
(2, 'Одобрена'),
(3, 'Отклонена')
ON DUPLICATE KEY UPDATE name=name;

-- Накатываем тестовые жанры для удобства проверки
INSERT INTO genres (name) VALUES 
('Фантастика'), ('Детектив'), ('Роман'), ('Ужасы'), ('Техническая литература')
ON DUPLICATE KEY UPDATE name=name;