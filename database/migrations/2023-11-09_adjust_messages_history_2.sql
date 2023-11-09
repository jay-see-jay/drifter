ALTER TABLE messages_labels_history
	ADD KEY label_pk_idx (label_pk),
DROP
label_id;

ALTER TABLE messages_labels
DROP
PRIMARY KEY,
	ADD PRIMARY KEY (label_pk, message_id),
ADD KEY label_pk_idx (label_pk);

ALTER TABLE history
DROP
PRIMARY KEY,
	ADD PRIMARY KEY (id, user_pk);