# ZhihuSpider
User spider for www.zhihu.com

顺带推荐一个付费好用的代理：[SmartProxy 全球IP代理](https://www.smartproxy.cn/regist?invite=HV8QHR)1亿真实住宅IP资源。
专业海外http代理商，千万优质纯净住宅IP资源，覆盖全球城市，高匿稳定提供100%原生住宅IP，支持社交账户，电商平台，网络数据收集等服务。
成功率伪装度超高！！本人测试用过之后感觉速度确实嘎嘎快，很给力。
搞跨境电商的用户可以用来tiktok养号，每个月还会更新一次代理IP池~
付费套餐多种多样，现在春季价格优惠，只要65折！
需要高质量代理IP的可以注册后联系客服，[实名注册后赠送500M流量](https://www.smartproxy.cn/regist?invite=HV8QHR)，不懂怎么用的同学可以问客服或者看视频教程。（官网有很多简单易懂的视频教学）

- 超高并发备份：独享高性能服务器，以真实住宅地址进行请求访问，保持代理正常连接，不限制并发数量，降低业务成本，提高运行效率。
- 优质IP资源：整合真实家庭住宅IP，汇聚IP资源池，不断更新IP，来自全球各个国家地区进行访问。自有数据节点，网络集成快捷。
- 形式多样：多种代理认证模式，帮助账户灵活设置，账密模式通过region参数添加制定国家城市；API白名单模式通过API链接获取即可。
- 技术服务：支持业务场景定制独享IP，千兆超高速带宽，出口IP可定制时效提供获取流量使用报告，追踪流量记录。  

<div align=center>
   <img src="https://user-images.githubusercontent.com/29977021/228770306-6c5d0b8a-c381-4be3-b500-e43fc47298b3.png" width="400px">
</div>

专属注册链接：[https://www.smartproxy.cn/regist](https://www.smartproxy.cn/regist?invite=HV8QHR)

## 1.Install python3 and packages
Make sure you have installed python3.
Using pip to install dependencies.
``` bash
pip install Image requests beautifulsoup4 html5lib redis PyMySQL 
```
## 2.Database Config
Install `mysql`,create your database.
Import `init.sql` to create your table.

## 3.Install redis
``` bash
# (ubuntu)
apt-get install redis

# or (centos)

yum install redis

# or (macos)
brew install redis
```
## 4.Config your application
Complete config.ini

## 5.Get start
``` bash
python get_user.py

# or command python3

python3 get_user.py
```

## 中文

在我的博客里有代码的详细解读：[我用python爬了知乎一百万用户的数据](http://www.jwlchina.cn/2016/11/04/%E6%88%91%E7%94%A8python%E7%88%AC%E4%BA%86%E7%9F%A5%E4%B9%8E%E4%B8%80%E7%99%BE%E4%B8%87%E7%94%A8%E6%88%B7%E7%9A%84%E6%95%B0%E6%8D%AE/)

数据统计分析：[百万知乎用户数据分析](http://zhihu.jwlchina.cn/)
# 这是一个多线程抓取知乎用户的程序

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
pip install Image requests beautifulsoup4 html5lib redis PyMySQL 
```

运行环境需要支持中文

测试运行环境python3.5，不保证其他运行环境能完美运行

1.**需要安装mysql和redis**

2.**配置`config.ini`文件，设置好mysql和redis，并且填写你的知乎帐号（master分支新版爬虫不需要登陆，但是可能会有时效问题，可以切换至new-ui分支使用）**

可以通过配置`config.ini`文件下的`[sys]` `sleep_time` 控制爬虫速度（尽量使用推荐值，过快容易被知乎封禁），`thread_num`配置线程数目

3.**向数据库导入`init.sql`**

# Run

开始抓取数据:`python get_user.py`
查看抓取数量:`python check_redis.py`

# 效果
![效果图1](http://www.jwlchina.cn/uploads/%E7%9F%A5%E4%B9%8E%E7%94%A8%E6%88%B7%E7%88%AC%E8%99%AB4.png)
![效果图2](http://www.jwlchina.cn/uploads/%E7%9F%A5%E4%B9%8E%E7%94%A8%E6%88%B7%E7%88%AC%E8%99%AB5.png)

# Docker

嫌麻烦的可以参考一下我用docker简单的搭建一个基础环境：
mysql和redis都是官方镜像
```bash
docker run --name mysql -itd mysql:latest
docker run --name redis -itd redis:latest
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

# 捐赠

您的支持是对我的最大鼓励！
谢谢你请我吃糖
![wechatpay](http://blog-image.jwlchina.cn/kong36088/kong36088.github.io/master/uploads/site/wechat-pay.png)
![alipay](http://blog-image.jwlchina.cn/kong36088/kong36088.github.io/master/uploads/site/zhifubao.jpg)
