# Requirements

需要用到的包：
`beautifulsoup4`
`html5lib`
`image`
`requests`
`redis`
`PyMySQL`

pip安装所有依赖包：
``` bash
pip install \
Image \
requests \
beautifulsoup4 \
html5lib \
redis \
PyMySQL
```

运行环境需要支持中文

测试运行环境python3.5，不保证其他运行环境能完美运行

**需要安装mysql和redis**

**配置`config.ini`文件**

**向数据库导入`init.sql`**

# Run

开始抓取数据:`python get_user.py`


# Docker

用docker简单的搭建一个基础环境：
mysql和redis都是官方镜像
```bash
docker run --name mysql -itd mysql:latest
docker run --name redis -itd mysql:latest
```


再利用docker-compose运行python镜像，我的python的docker-compose.yml：
``` bash
python:
    container_name: python
    build: .
    ports:
      - "84:80"
    external_links:
      - memcache:memcache
      - mysql:mysql
      - redis:redis
    volumes:
      - /docker_containers/python/www:/var/www/html
    tty: true
    stdin_open: true
    extra_hosts:
      - "python:192.168.102.140"
    environment:
        PYTHONIOENCODING: utf-8
```
我的Dockerfile：
``` bash
From kong36088/zhihu-spider:latest
```

