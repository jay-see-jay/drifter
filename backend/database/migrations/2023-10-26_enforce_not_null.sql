ALTER TABLE history
	MODIFY COLUMN user_pk int NOT NULL;

ALTER TABLE threads
	MODIFY COLUMN history_id varchar (255) NOT NULL,
	MODIFY COLUMN user_pk int NOT NULL;

ALTER TABLE labels
	MODIFY COLUMN user_pk int NOT NULL;