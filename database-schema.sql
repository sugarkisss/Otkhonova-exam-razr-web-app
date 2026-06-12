CREATE TABLE roles (
	id INTEGER NOT NULL, 
	name VARCHAR(50) NOT NULL, 
	description TEXT NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (name)
);
CREATE TABLE genres (
	id INTEGER NOT NULL, 
	name VARCHAR(100) NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (name)
);
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
CREATE TABLE review_statuses (
	id INTEGER NOT NULL, 
	name VARCHAR(50) NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (name)
);
CREATE TABLE books_genres (
	book_id INTEGER NOT NULL, 
	genre_id INTEGER NOT NULL, 
	PRIMARY KEY (book_id, genre_id), 
	FOREIGN KEY(book_id) REFERENCES books (id) ON DELETE CASCADE, 
	FOREIGN KEY(genre_id) REFERENCES genres (id) ON DELETE CASCADE
);
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
CREATE TABLE covers (
	id INTEGER NOT NULL, 
	filename VARCHAR(255) NOT NULL, 
	mime_type VARCHAR(100) NOT NULL, 
	md5_hash VARCHAR(32) NOT NULL, 
	book_id INTEGER NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(book_id) REFERENCES books (id) ON DELETE CASCADE
);
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
