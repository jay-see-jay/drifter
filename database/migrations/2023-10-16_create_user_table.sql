CREATE TABLE users
(
	pk               int          NOT NULL AUTO_INCREMENT,
	email            varchar(255) NOT NULL,
	is_active        tinyint(1) DEFAULT '0',
	created_at       datetime DEFAULT current_timestamp(),
	access_token     varchar(2048),
	refresh_token    varchar(512),
	token_expires_at datetime,
);
