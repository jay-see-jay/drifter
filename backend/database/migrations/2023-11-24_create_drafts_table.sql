CREATE TABLE drafts
(
	id         varchar(255) NOT NULL PRIMARY KEY,
	created_at datetime DEFAULT current_timestamp(),
	message_id varchar(255) NOT NULL,
	thread_id  varchar(255) NOT NULL,
	user_pk    int          NOT NULL,
	KEY        user_pk_idx (user_pk),
	KEY        message_id_idx (message_id),
	KEY        thread_id_idx (thread_id)
		.
);