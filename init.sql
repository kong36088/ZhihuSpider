CREATE TABLE IF NOT EXISTS `user` (
	`url` VARCHAR(100) NOT NULL COMMENT '知乎个人的短url',
	`nickname` VARCHAR(100) NOT NULL,
	`self_domain` VARCHAR(100) NOT NULL COMMENT '个人的个性化域名',
	`user_type` VARCHAR(50) NOT NULL COMMENT '个人or企业',
	`gender` INT(1) NOT NULL DEFAULT 1 COMMENT '0女1男-1未知',
	`follower` INT(11) NOT NULL COMMENT '粉丝人数',
	`following` INT(11) NOT NULL COMMENT '关注人数',
	`agree_num` INT(11) NOT NULL COMMENT '赞同数',
	`appreciate_num` INT(11) NOT NULL COMMENT '感谢数',
	`star_num` INT(11) NOT NULL COMMENT '答案收藏数',
	`share_num` INT(11) NOT NULL COMMENT '分享数',
	`browse_num` INT(11) NOT NULL COMMENT '浏览数',
  `trade` VARCHAR(50) NOT NULL COMMENT '行业',
	`company` VARCHAR(50) NOT NULL COMMENT '公司',
	`school` VARCHAR(50) NOT NULL COMMENT '学校',
	`major` VARCHAR(50) NOT NULL COMMENT '专业',
	`job` VARCHAR(50) NOT NULL COMMENT '工作',
  `location` VARCHAR(50) NOT NULL COMMENT '位置',
	`description` VARCHAR(100) NOT NULL COMMENT '一句话介绍自己',
	`update_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `ask_num` INT(11) NOT NULL COMMENT '提问数',
  `answer_num` INT(11) NOT NULL COMMENT '回答数',
  `article_num` INT(11) NOT NULL COMMENT '文章数',
  `collect_num` INT(11) NOT NULL COMMENT '自己的收藏数',
  `public_edit_num` INT(11) NOT NULL COMMENT '公共编辑数',
	PRIMARY KEY (`url`)
)
COLLATE='utf8_general_ci'
ENGINE=MyISAM
;
