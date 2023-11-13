ALTER TABLE history
DROP
temp_pk;

ALTER TABLE messages_labels
DROP
label_id,
DROP INDEX label_pk;