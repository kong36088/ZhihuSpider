# -*- coding: utf-8 -*-
from login.login import Login as Login
import requests
import http.cookiejar as cookielib
import configparser
from bs4 import BeautifulSoup
import sys
import redis
import json
import math
import re
import pymysql
import traceback
import threading


class GetUser(threading.Thread):
    session = ''
    config = ''
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/53.0.2785.143 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Host": "www.zhihu.com",
        "Referer": "https://www.zhihu.com/",
        "Origin": "https://www.zhihu.com/",
        "Upgrade-Insecure-Requests": "1",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "Pragma": "no-cache",
        "Accept-Encoding": "gzip, deflate, br",
        'Connection': 'close'
    }
    retry = 0  # 重试次数
    redis_con = ''
    counter = 0  # 被抓取用户计数
    xsrf = ''
    db = ''
    db_cursor = ''
    counter = 0  # 记录多少用户被抓取
    max_queue_len = 1000  # redis带抓取用户队列最大长度

    def __init__(self, threadID=1, name=''):
        # 多线程
        print("线程" + str(threadID) + "初始化")
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name
        try:
            print("线程" + str(threadID) + "初始化成功")
        except Exception as err:
            print(err)
            print("线程" + str(threadID) + "开启失败")

        self.threadLock = threading.Lock()

        # 获取配置
        self.config = configparser.ConfigParser()
        self.config.read("config.ini")

        # 初始化session
        requests.adapters.DEFAULT_RETRIES = 5
        self.session = requests.Session()
        self.session.cookies = cookielib.LWPCookieJar(filename='cookie')
        self.session.keep_alive = False
        try:
            self.session.cookies.load(ignore_discard=True)
        except:
            print('Cookie 未能加载')
        finally:
            pass

        # 创建login对象
        lo = Login(self.session)
        lo.do_login()

        # 初始化redis连接
        try:
            redis_host = self.config.get("redis", "host")
            redis_port = self.config.get("redis", "port")
            self.redis_con = redis.Redis(host=redis_host, port=redis_port, db=0)
            # 刷新redis库
            # self.redis_con.flushdb()
        except:
            print("请安装redis或检查redis连接配置")
            sys.exit()

        # 初始化数据库连接
        try:
            db_host = self.config.get("db", "host")
            db_port = int(self.config.get("db", "port"))
            db_user = self.config.get("db", "user")
            db_pass = self.config.get("db", "password")
            db_db = self.config.get("db", "db")
            db_charset = self.config.get("db", "charset")
            self.db = pymysql.connect(host=db_host, port=db_port, user=db_user, passwd=db_pass, db=db_db,
                                      charset=db_charset)
            self.db_cursor = self.db.cursor()
        except:
            print("请检查数据库配置")
            sys.exit()

        # 初始化系统设置
        self.max_queue_len = int(self.config.get("sys", "max_queue_len"))

    # 获取首页html
    def get_index_page(self):
        index_url = 'https://www.zhihu.com/'
        try:
            index_html = self.session.get(index_url, headers=self.headers, timeout=35)
        except Exception as err:
            # 出现异常重试
            print("获取页面失败，正在重试......")
            print(err)
            traceback.print_exc()
            return None
        finally:
            pass
        return index_html.text

    # 获取单个用户详情页面
    def get_user_page(self, name_url):
        user_page_url = 'https://www.zhihu.com' + str(name_url) + '/about'
        try:
            index_html = self.session.get(user_page_url, headers=self.headers, timeout=35)
        except Exception as err:
            # 出现异常重试
            print("失败name_url：" + str(name_url) + "获取页面失败，放弃该用户")
            print(err)
            traceback.print_exc()
            return None
        finally:
            pass
        return index_html.text

    # 获取粉丝页面
    def get_follower_page(self, name_url):
        user_page_url = 'https://www.zhihu.com' + str(name_url) + '/followers'
        try:
            index_html = self.session.get(user_page_url, headers=self.headers, timeout=35)
        except Exception as err:
            # 出现异常重试
            print("失败name_url：" + str(name_url) + "获取页面失败，放弃该用户")
            print(err)
            traceback.print_exc()
            return None
        finally:
            pass
        return index_html.text

    def get_following_page(self, name_url):
        user_page_url = 'https://www.zhihu.com' + str(name_url) + '/followers'
        try:
            index_html = self.session.get(user_page_url, headers=self.headers, timeout=35)
        except Exception as err:
            # 出现异常重试
            print("失败name_url：" + str(name_url) + "获取页面失败，放弃该用户")
            print(err)
            traceback.print_exc()
            return None
        finally:
            pass
        return index_html.text

    # 获取首页上的用户列表，存入redis
    def get_index_page_user(self):
        index_html = self.get_index_page()
        if not index_html:
            return
        BS = BeautifulSoup(index_html, "html.parser")
        self.get_xsrf(index_html)
        user_a = BS.find_all("a", class_="author-link")  # 获取用户的a标签
        for a in user_a:
            if a:
                self.add_wait_user(a.get('href'))
            else:
                continue

    # 加入带抓取用户队列，先用redis判断是否已被抓取过
    def add_wait_user(self, name_url):
        # 判断是否已抓取
        self.threadLock.acquire()
        if not self.redis_con.hexists('already_get_user', name_url):
            self.counter += 1
            print(name_url + " 加入队列")
            self.redis_con.hset('already_get_user', name_url, 1)
            self.redis_con.lpush('user_queue', name_url)
            print("添加用户 " + name_url + "到队列")
        self.threadLock.release()

    # 获取页面出错移出redis
    def del_already_user(self, name_url):
        self.threadLock.acquire()
        if not self.redis_con.hexists('already_get_user', name_url):
            self.counter -= 1
            self.redis_con.hdel('already_get_user', name_url)
        self.threadLock.release()

    # 分析粉丝页面获取用户的所有粉丝用户
    # @param follower_page get_follower_page()中获取到的页面，这里获取用户hash_id请求粉丝接口获取粉丝信息
    def get_all_follower(self, name_url):
        follower_page = self.get_follower_page(name_url)
        # 判断是否获取到页面
        if not follower_page:
            return

        BS = BeautifulSoup(follower_page, 'html.parser')
        # 获取关注者数量
        follower_num = int(BS.find('span', text='关注者').find_parent().find('strong').get_text())
        # 获取用户的hash_id
        hash_id = \
            json.loads(BS.select("#zh-profile-follows-list")[0].select(".zh-general-list")[0].get('data-init'))[
                'params'][
                'hash_id']

        # 获取关注者列表
        self.get_xsrf(follower_page)  # 获取xsrf
        post_url = 'https://www.zhihu.com/node/ProfileFollowersListV2'
        # 开始获取所有的关注者 math.ceil(follower_num/20)*20
        for i in range(0, math.ceil(follower_num / 20) * 20, 20):
            post_data = {
                'method': 'next',
                'params': json.dumps({"offset": i, "order_by": "created", "hash_id": hash_id})
            }
            try:
                j = self.session.post(post_url, params=post_data, headers=self.headers, timeout=35).text.encode(
                    'latin-1').decode(
                    'unicode-escape')
                pattern = re.compile(r"class=\"zm-item-link-avatar\"[^\"]*\"([^\"]*)", re.DOTALL)
                j = pattern.findall(j)
                for user in j:
                    user = user.replace('\\', '')
                    self.add_wait_user(user)  # 保存到redis
            except Exception as err:
                print("获取正在关注失败")
                print(err)
                traceback.print_exc()
                pass

    # 获取正在关注列表
    def get_all_following(self, name_url):
        following_page = self.get_following_page(name_url)
        # 判断是否获取到页面
        if not following_page:
            return
        BS = BeautifulSoup(following_page, 'html.parser')
        # 获取关注者数量
        following_num = int(BS.find('span', text='关注了').find_parent().find('strong').get_text())
        # 获取用户的hash_id
        hash_id = \
            json.loads(BS.select("#zh-profile-follows-list")[0].select(".zh-general-list")[0].get('data-init'))[
                'params'][
                'hash_id']

        # 获取关注者列表
        self.get_xsrf(following_page)  # 获取xsrf
        post_url = 'https://www.zhihu.com/node/ProfileFolloweesListV2'
        # 开始获取所有的关注者 math.ceil(follower_num/20)*20
        for i in range(0, math.ceil(following_num / 20) * 20, 20):
            post_data = {
                'method': 'next',
                'params': json.dumps({"offset": i, "order_by": "created", "hash_id": hash_id})
            }
            try:
                j = self.session.post(post_url, params=post_data, headers=self.headers, timeout=35).text.encode(
                    'latin-1').decode(
                    'unicode-escape')
                pattern = re.compile(r"class=\"zm-item-link-avatar\"[^\"]*\"([^\"]*)", re.DOTALL)
                j = pattern.findall(j)
                for user in j:
                    user = user.replace('\\', '')
                    self.add_wait_user(user)  # 保存到redis
            except Exception as err:
                print("获取正在关注失败")
                print(err)
                traceback.print_exc()
                pass

    # 分析about页面，获取用户详细资料
    def get_user_info(self, name_url):
        about_page = self.get_user_page(name_url)
        # 判断是否获取到页面
        if not about_page:
            print("获取用户详情页面失败，跳过，name_url：" + name_url)
            return

        self.get_xsrf(about_page)

        BS = BeautifulSoup(about_page, 'html.parser')
        # 获取页面的具体数据
        try:
            nickname = BS.find("a", class_="name").get_text() if BS.find("a", class_="name") else ''
            user_type = name_url[1:name_url.index('/', 1)]
            self_domain = name_url[name_url.index('/', 1) + 1:]
            gender = 2 if BS.find("i", class_="icon icon-profile-female") else (1 if BS.find("i", class_="icon icon-profile-male") else 3)
            follower_num = int(BS.find('span', text='关注者').find_parent().find('strong').get_text())
            following_num = int(BS.find('span', text='关注了').find_parent().find('strong').get_text())
            agree_num = int(re.findall(r'<strong>(.*)</strong>.*赞同', about_page)[0])
            appreciate_num = int(re.findall(r'<strong>(.*)</strong>.*感谢', about_page)[0])
            star_num = int(re.findall(r'<strong>(.*)</strong>.*收藏', about_page)[0])
            share_num = int(re.findall(r'<strong>(.*)</strong>.*分享', about_page)[0])
            browse_num = int(BS.find_all("span", class_="zg-gray-normal")[2].find("strong").get_text())
            trade = BS.find("span", class_="business item").get('title') if BS.find("span", class_="business item") else ''
            company = BS.find("span", class_="employment item").get('title') if BS.find("span", class_="employment item") else ''
            school = BS.find("span", class_="education item").get('title') if BS.find("span", class_="education item") else ''
            major = BS.find("span", class_="education-extra item").get('title') if BS.find("span", class_="education-extra item") else ''
            job = BS.find("span", class_="position item").get_text() if BS.find("span", class_="position item") else ''
            location = BS.find("span", class_="location item").get('title') if BS.find("span", class_="location item") else ''
            description = BS.find("div", class_="bio ellipsis").get('title') if BS.find("div", class_="bio ellipsis") else ''
            ask_num = int(BS.find_all("a", class_='item')[1].find("span").get_text()) if \
                BS.find_all("a", class_='item')[
                    1] else int(0)
            answer_num = int(BS.find_all("a", class_='item')[2].find("span").get_text()) if \
                BS.find_all("a", class_='item')[
                    2] else int(0)
            article_num = int(BS.find_all("a", class_='item')[3].find("span").get_text()) if \
                BS.find_all("a", class_='item')[3] else int(0)
            collect_num = int(BS.find_all("a", class_='item')[4].find("span").get_text()) if \
                BS.find_all("a", class_='item')[4] else int(0)
            public_edit_num = int(BS.find_all("a", class_='item')[5].find("span").get_text()) if \
                BS.find_all("a", class_='item')[5] else int(0)

            replace_data = \
                (pymysql.escape_string(name_url), nickname, self_domain, user_type,
                 gender, follower_num, following_num, agree_num, appreciate_num, star_num, share_num, browse_num,
                 trade, company, school, major, job, location, pymysql.escape_string(description),
                 ask_num, answer_num, article_num, collect_num, public_edit_num)

            replace_sql = '''REPLACE INTO
                          user(url,nickname,self_domain,user_type,
                          gender, follower,following,agree_num,appreciate_num,star_num,share_num,browse_num,
                          trade,company,school,major,job,location,description,
                          ask_num,answer_num,article_num,collect_num,public_edit_num)
                          VALUES(%s,%s,%s,%s,
                          %s,%s,%s,%s,%s,%s,%s,%s,
                          %s,%s,%s,%s,%s,%s,%s,
                          %s,%s,%s,%s,%s)'''

            try:
                print("获取到数据：")
                print(replace_data)
                self.db_cursor.execute(replace_sql, replace_data)
                self.db.commit()
            except Exception as err:
                print("插入数据库出错")
                print("获取到数据：")
                print(replace_data)
                print("插入语句：" + self.db_cursor._last_executed)
                self.db.rollback()
                print(err)
                traceback.print_exc()

        except Exception as err:
            print("获取数据出错，跳过用户")
            self.redis_con.hdel("already_get_user", name_url)
            self.del_already_user(name_url)
            print(err)
            traceback.print_exc()
            pass

    # 获取xsrf保存到header
    def get_xsrf(self, html):
        if self.xsrf:
            return self.xsrf
        BS = BeautifulSoup(html, 'html.parser')
        xsrf_input = BS.find("input", attrs={'name': '_xsrf'})
        self.xsrf = xsrf_input.get("value")
        self.headers['X-Xsrftoken'] = self.xsrf
        self.session.cookies.save()
        print("获取到xsrf：" + self.xsrf)

    # 开始抓取用户，程序总入口
    def entrance(self):
        while 1:
            if int(self.redis_con.llen("user_queue")) < 1:
                self.get_index_page_user()
            else:
                # 出队列获取用户name_url redis取出的是byte，要decode成utf-8
                name_url = str(self.redis_con.rpop("user_queue").decode('utf-8'))
                print("正在处理name_url：" + name_url)
                self.get_user_info(name_url)
                if int(self.redis_con.llen("user_queue")) <= int(self.max_queue_len):
                    self.get_all_follower(name_url)
                    self.get_all_following(name_url)
            self.session.cookies.save()

    def run(self):
        print(self.name + " is running")
        self.entrance()


if __name__ == '__main__':
    login = GetUser(999, "登陆线程")

    threads = []
    for i in range(0, 4):
        m = GetUser(i, "thread" + str(i))
        threads.append(m)

    for i in range(0, 4):
        threads[i].start()

    for i in range(0, 4):
        threads[i].join()
