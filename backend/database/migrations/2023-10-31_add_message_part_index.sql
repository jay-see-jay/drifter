ALTER TABLE message_parts
DROP
COLUMN id,
	ADD COLUMN pk INT NOT NULL PRIMARY KEY FIRST,
	ADD COLUMN part_index INT AFTER message_id;