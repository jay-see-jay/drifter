ALTER TABLE message_parts
DROP
COLUMN temp_pk,
  MODIFY COLUMN pk INT NOT NULL AUTO_INCREMENT;