PRAGMA foreign_keys=OFF;
BEGIN TRANSACTION;
CREATE TABLE roles (
	id INTEGER NOT NULL, 
	name VARCHAR(50) NOT NULL, 
	description TEXT NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (name)
);
INSERT INTO roles VALUES(1,'Администратор','Полный доступ к системе');
INSERT INTO roles VALUES(2,'Модератор','Модерация рецензий и правка книг');
INSERT INTO roles VALUES(3,'Пользователь','Обычный читатель, пишет отзывы');
CREATE TABLE genres (
	id INTEGER NOT NULL, 
	name VARCHAR(100) NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (name)
);
INSERT INTO genres VALUES(1,'Фантастика');
INSERT INTO genres VALUES(2,'Детектив');
INSERT INTO genres VALUES(3,'Роман');
INSERT INTO genres VALUES(4,'Техническая литература');
CREATE TABLE books (
	id INTEGER NOT NULL, 
	title VARCHAR(255) NOT NULL, 
	description TEXT NOT NULL, 
	year INTEGER NOT NULL, 
	publisher VARCHAR(255) NOT NULL, 
	author VARCHAR(255) NOT NULL, 
	pages INTEGER NOT NULL, 
	PRIMARY KEY (id)
);
INSERT INTO books VALUES(1,'Чистый код',replace('Эта книга посвящена хорошему программированию. Она полна реальных примеров кода.\n\nПосле чтения вы узнаете:\n* Как отличать **хороший код** от плохого.\n* Как писать качественный код и как преобразовывать плохой код в хороший.\n* Правила создания хороших *имен, функций, объектов и классов*.','\n',char(10)),2019,'Питер','Роберт Мартин',464);
INSERT INTO books VALUES(3,'Автостопом по галактике',replace('Знаменитый фантастический роман с тонким английским юмором.\n\nГлавные правила путешественника:\n* Никогда не паникуйте!\n* Всегда носите с собой **полотенце**.\n\n*Артур Дент* и его друг Форд Префект отправляются в безумное странствие по Вселенной после уничтожения Земли.','\n',char(10)),2020,'АСТ','Дуглас Адамс',320);
INSERT INTO books VALUES(4,'Записки о Шерлоке Холмсе',replace('Сборник классических историй о величайшем сыщике.\n\nШерлок Холмс использует свой знаменитый **дедуктивный метод** для раскрытия:\n1. Загадочных преступлений в туманном Лондоне.\n2. Сложных семейных тайн.\n\nКаждая история — это *шедевр аналитики* и логики.','\n',char(10)),2021,'Эксмо','Артур Конан Дойл',544);
INSERT INTO books VALUES(5,'1984',replace('Культовый роман-антиутопия о тоталитарном обществе.\n\nГлавные лозунги государства:\n* **Война — это мир**\n* **Свобода — это рабство**\n* **Незнание — сила**\n\nИстория Уинстона Смита, который пытается сохранить *каплю индивидуальности* в мире полного контроля.','\n',char(10)),2018,'АСТ','Джордж Оруэлл',320);
INSERT INTO books VALUES(7,'Дюна',replace('Эпическая сага о пустынной планете *Арракис*.\n\nЗдесь добывают самое ценное вещество во Вселенной — **пряность (меланж)**.\n* Борьба великих домов за власть.\n* Таинственные пророчества.\n* Огромные песчаные черви.','\n',char(10)),2022,'АСТ','Фрэнк Герберт',704);
INSERT INTO books VALUES(8,'Мастер и Маргарита',replace('Markdown\nБессмертный шедевр русской литературы, сочетающий мистику, сатиру и философию.\n\nТри переплетающиеся линии сюжета:\n1. Визит **Воланда** и его свиты в Москву 1930-х годов.\n2. История трагической любви *Мастера и Маргариты*.\n3. Библейские главы о Понтии Пилате.','\n',char(10)),2019,'Азбука','Михаил Булгаков',480);
CREATE TABLE review_statuses (
	id INTEGER NOT NULL, 
	name VARCHAR(50) NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (name)
);
INSERT INTO review_statuses VALUES(1,'На рассмотрении');
INSERT INTO review_statuses VALUES(2,'Одобрена');
INSERT INTO review_statuses VALUES(3,'Отклонена');
CREATE TABLE books_genres (
	book_id INTEGER NOT NULL, 
	genre_id INTEGER NOT NULL, 
	PRIMARY KEY (book_id, genre_id), 
	FOREIGN KEY(book_id) REFERENCES books (id) ON DELETE CASCADE, 
	FOREIGN KEY(genre_id) REFERENCES genres (id) ON DELETE CASCADE
);
INSERT INTO books_genres VALUES(1,4);
INSERT INTO books_genres VALUES(3,1);
INSERT INTO books_genres VALUES(4,2);
INSERT INTO books_genres VALUES(5,3);
INSERT INTO books_genres VALUES(7,1);
INSERT INTO books_genres VALUES(8,3);
CREATE TABLE users (
	id INTEGER NOT NULL, 
	login VARCHAR(50) NOT NULL, 
	password_hash VARCHAR(255) NOT NULL, 
	last_name VARCHAR(50) NOT NULL, 
	first_name VARCHAR(50) NOT NULL, 
	middle_name VARCHAR(50), 
	role_id INTEGER NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (login), 
	FOREIGN KEY(role_id) REFERENCES roles (id)
);
INSERT INTO users VALUES(1,'admin','admin','Петров','Алексей',NULL,1);
INSERT INTO users VALUES(2,'moderator','mod','Сидоров','Николай',NULL,2);
INSERT INTO users VALUES(3,'user','user','Иванова','Мария',NULL,3);
CREATE TABLE covers (
	id INTEGER NOT NULL, 
	filename VARCHAR(255) NOT NULL, 
	mime_type VARCHAR(100) NOT NULL, 
	md5_hash VARCHAR(32) NOT NULL, 
	book_id INTEGER NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(book_id) REFERENCES books (id) ON DELETE CASCADE
);
INSERT INTO covers VALUES(1,'57b8f3735f27536fba5e7ff59048995a.jpg','image/jpeg','57b8f3735f27536fba5e7ff59048995a',1);
INSERT INTO covers VALUES(3,'37ac3e3800eb2f5fbff4a0d6272202c0.jpg','image/jpeg','37ac3e3800eb2f5fbff4a0d6272202c0',3);
INSERT INTO covers VALUES(4,'75067426267180db59a684bdfb93e172.jpg','image/jpeg','75067426267180db59a684bdfb93e172',4);
INSERT INTO covers VALUES(5,'17f050c9748c7479d1a20868b4c6f4ea.jpg','image/jpeg','17f050c9748c7479d1a20868b4c6f4ea',5);
INSERT INTO covers VALUES(7,'a19659b2a12483c09f5a0e994ea6589c.jpg','image/jpeg','a19659b2a12483c09f5a0e994ea6589c',7);
INSERT INTO covers VALUES(8,'37aa1b0109ff57285f21d635d1877ffc.jpg','image/jpeg','37aa1b0109ff57285f21d635d1877ffc',8);
CREATE TABLE reviews (
	id INTEGER NOT NULL, 
	book_id INTEGER NOT NULL, 
	user_id INTEGER NOT NULL, 
	rating INTEGER NOT NULL, 
	text TEXT NOT NULL, 
	created_at DATETIME NOT NULL, 
	status_id INTEGER NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(book_id) REFERENCES books (id) ON DELETE CASCADE, 
	FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE, 
	FOREIGN KEY(status_id) REFERENCES review_statuses (id)
);
INSERT INTO reviews VALUES(2,5,3,3,'очень хорошая книга!!!!','2026-06-11 19:47:09.752335',3);
INSERT INTO reviews VALUES(3,8,2,3,'очень хорошая книга!!!!','2026-06-11 19:32:54.874762',3);
INSERT INTO reviews VALUES(4,8,3,5,'суперская книга! сюжет очень классный','2026-06-11 19:34:24.341235',2);
COMMIT;
