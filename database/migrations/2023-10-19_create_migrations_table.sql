CREATE TABLE migrations
(
	pk           int         NOT NULL AUTO_INCREMENT PRIMARY KEY,
	name         varchar(50) NOT NULL,
	date         date        NOT NULL,
	date_name    varchar(100) UNIQUE DEFAULT (CONCAT(date, '_', name)),
	completed_at datetime
);