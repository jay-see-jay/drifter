CREATE TABLE message_parts
(
	id                     varchar(255) NOT NULL PRIMARY KEY,
	user_pk                int          NOT NULL,
	KEY                    user_pk_idx (user_pk),
	message_id             varchar(255),
	KEY                    message_id_idx (message_id),
	mime_type              varchar(255) NOT NULL,
	filename               varchar(255) NOT NULL,
	body_attachment_id     varchar(255),
	body_size              int,
	body_data              text,
	parent_message_part_id varchar(255),
	KEY                    parent_message_part_id_idx (parent_message_part_id)
);

CREATE TABLE message_headers
(
	pk              int          NOT NULL AUTO_INCREMENT PRIMARY KEY,
	message_part_id varchar(255) NOT NULL,
	KEY             message_part_id_idx (message_part_id),
	name            varchar(255) NOT NULL,
	value           varchar(255) NOT NULL
);

CREATE TABLE messages_labels_history
(
	pk         int          NOT NULL AUTO_INCREMENT PRIMARY KEY,
	history_id varchar(255) NOT NULL,
	KEY        history_id_idx (history_id),
	message_id varchar(255) NOT NULL,
	KEY        message_id_idx (message_id),
	label_id   varchar(255) NOT NULL,
	KEY        label_id_idx (label_id),
	changed_at datetime     NOT NULL,
	action     ENUM('added', 'removed') NOT NULL
);

CREATE TABLE messages_labels
(
	label_id   varchar(255) NOT NULL,
	message_id varchar(255) NOT NULL,
	PRIMARY KEY (label_id, message_id),
	KEY        label_id_idx (label_id),
	KEY        message_id_idx (message_id)
);

CREATE TABLE messages
(
	id                 varchar(255) NOT NULL PRIMARY KEY,
	snippet            text,
	user_pk            int          NOT NULL,
	KEY                user_pk_idx (user_pk),
	thread_id          varchar(255) NOT NULL,
	KEY                thread_id_idx (thread_id),
	history_id         varchar(255) NOT NULL,
	KEY                history_id_idx (history_id),
	internal_date      datetime,
	added_history_id   varchar(255) NOT NULL,
	KEY                added_history_id_idx (added_history_id),
	size_estimate      int,
	raw                text,
	deleted_at         datetime,
	deleted_history_id varchar(255),
	KEY                deleted_history_id_idx (deleted_history_id),
	message_part_id    varchar(255) NOT NULL,
	KEY                message_part_id_idx (message_part_id)
);

CREATE TABLE messages_history
(
	history_id varchar(255) NOT NULL,
	message_id varchar(255) NOT NULL,
	PRIMARY KEY (history_id, message_id),
	KEY        history_id_idx (history_id),
	KEY        message_id_idx (message_id)
);