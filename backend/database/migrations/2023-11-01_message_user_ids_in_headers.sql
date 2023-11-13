ALTER TABLE message_headers
	ADD COLUMN user_pk INT NOT NULL AFTER pk,
	ADD COLUMN message_id varchar(255) NOT NULL AFTER user_pk,
	MODIFY message_part_id varchar (50),
	MODIFY value text NOT NULL,
	ADD UNIQUE KEY (message_id, message_part_id, name);