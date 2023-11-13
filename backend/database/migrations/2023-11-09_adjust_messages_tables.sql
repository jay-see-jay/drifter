ALTER TABLE messages_labels
	MODIFY label_pk int NOT NULL,
	ADD UNIQUE KEY label_pk (label_pk);

ALTER TABLE messages
DROP
deleted_at;

ALTER TABLE messages_labels_history
DROP
changed_at,
	ADD COLUMN label_pk int NOT NULL;

ALTER TABLE history
	ADD COLUMN temp_pk int AUTO_INCREMENT NOT NULL UNIQUE KEY;