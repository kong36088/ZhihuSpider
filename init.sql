CREATE TABLE IF NOT EXISTS `user` (
	`id` INT(11) NOT NULL AUTO_INCREMENT,
	`nickname` VARCHAR(100) NOT NULL,
	`url` VARCHAR(100) NOT NULL COMMENT '知乎个人的短url',
	`self_domain` VARCHAR(100) NOT NULL COMMENT '个人的url路径',
	`user_type` VARCHAR(50) NOT NULL COMMENT '个人or企业',
	`gender` INT(1) NOT NULL,
	`follower` INT(11) NOT NULL COMMENT '粉丝人数',
	`following` INT(11) NOT NULL COMMENT '关注人数',
	`agree_num` INT(11) NOT NULL COMMENT '赞同数',
	`appreciate_num` INT(11) NOT NULL COMMENT '感谢数',
	`star_num` INT(11) NOT NULL COMMENT '收藏数',
	`share_num` INT(11) NOT NULL COMMENT '分享数',
	`browse_num` INT(11) NOT NULL,
	`company` VARCHAR(50) NOT NULL,
	`education` VARCHAR(50) NOT NULL,
	`job` VARCHAR(50) NOT NULL,
	`location` VARCHAR(50) NOT NULL,
	`update_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
	PRIMARY KEY (`id`)
)
COLLATE='utf8_general_ci'
ENGINE=InnoDB
;
