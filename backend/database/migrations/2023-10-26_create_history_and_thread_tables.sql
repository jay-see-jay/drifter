CREATE TABLE history
(
	id           varchar(255) NOT NULL PRIMARY KEY,
	created_at   datetime DEFAULT current_timestamp(),
	processed_at datetime,
	user_pk      int,
	KEY          user_pk_idx (user_pk)
);

CREATE TABLE threads
(
	id         varchar(255) NOT NULL PRIMARY KEY,
	snippet    text,
	history_id varchar(255),
	KEY        history_id_idx (history_id),
	user_pk    int,
	KEY        user_pk_idx (user_pk)
);

CREATE TABLE labels
(
	id                      varchar(255) NOT NULL PRIMARY KEY,
	name                    text,
	message_list_visibility ENUM('show', 'hide'),
	label_list_visibility   ENUM('labelShow', 'labelShowIfUnread', 'labelHide'),
	type                    ENUM('system', 'user'),
	messages_total          int,
	messages_unread         int,
	threads_total           int,
	threads_unread          int,
	text_color              varchar(255),
	background_color        varchar(255),
	user_pk                 int,
	KEY                     user_pk_idx (user_pk)
);