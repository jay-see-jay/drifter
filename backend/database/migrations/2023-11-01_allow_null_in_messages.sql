ALTER TABLE messages
	MODIFY COLUMN added_history_id varchar (255) NULL,
DROP
COLUMN message_part_id,
DROP
COLUMN raw;