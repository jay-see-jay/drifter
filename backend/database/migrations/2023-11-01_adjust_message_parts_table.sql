ALTER TABLE message_parts
	MODIFY message_id varchar (255) NOT NULL,
	MODIFY body_attachment_id varchar (2048),
	MODIFY parent_message_part_id varchar (50),
	MODIFY filename varchar (255) NULL,
	CHANGE part_index part_id varchar (50),
	ADD UNIQUE KEY (message_id, part_id);