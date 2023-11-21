CREATE TABLE mailbox_subscriptions
(
	pk         int          NOT NULL AUTO_INCREMENT PRIMARY KEY,
	user_pk    int          NOT NULL,
	created_at datetime DEFAULT current_timestamp(),
	history_id varchar(255) NOT NULL,
	expiration datetime     NOT NULL
);
