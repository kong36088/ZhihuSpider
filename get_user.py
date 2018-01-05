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
import pymysql
import traceback
import threading
import time
import random

# 获取配置
cfg = configparser.ConfigParser()
cfg.read("config.ini")

class GetUser(threading.Thread):
    session = None
    config = None
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.108 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Host": "www.zhihu.com",
        "Referer": "https://www.zhihu.com/",
        "Origin": "https://www.zhihu.com/",
        "Upgrade-Insecure-Requests": "1",
        "Content-Type": "application/json, text/plain, */*",
        "Pragma": "no-cache",
        "Accept-Encoding": "gzip, deflate",
        'Connection': 'close',
        'authorization': 'oauth c3cef7c66a1843f8b3a9e6a1e3160e20',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    }

    retry = 0  # 重试次数
    redis_con = ''
    counter = 0  # 被抓取用户计数
    xsrf = ''
    db = None
    db_cursor = None
    max_queue_len = 1000  # redis带抓取用户队列最大长度
    ua = (
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_7_0) AppleWebKit/535.11 (KHTML, like Gecko) Chrome/17.0.963.56 Safari/535.11',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/53.0.2785.143 Safari/537.36',
        'Mozilla/5.0 (Windows; U; Windows NT 6.1; en-us) AppleWebKit/534.50 (KHTML, like Gecko) Version/5.1 Safari/534.50',
        'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; 360SE)',
    )
    sleep_time = 1

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
        self.config = cfg

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
        '''
        lo = Login(self.session)
        lo.do_login()
        '''

        # 初始化redis连接
        try:
            redis_host = self.config.get("redis", "host")
            redis_port = self.config.get("redis", "port")
            self.redis_con = redis.Redis(host=redis_host, port=redis_port, db=0)
            # 刷新redis库
            # self.redis_con.flushdb()
        except Exception as err:
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
        except Exception as err:
            print("请检查数据库配置")
            sys.exit()

        # 初始化系统设置
        self.max_queue_len = int(self.config.get("sys", "max_queue_len"))
        self.sleep_time = float(self.config.get("sys", "sleep_time"))

    # 获取首页html
    def get_index_page(self):
        index_url = 'https://www.zhihu.com/explore'
        try:
            index_html = self.session.get(index_url, headers=self.headers, timeout=35)
        except Exception as err:
            # 出现异常重试
            print("获取页面失败，正在重试......")
            print(err)
            traceback.print_exc()
            return None
        finally:
            self.save_cookie()
            pass
        return index_html.text

    # 获取首页上的用户列表，存入redis
    def get_index_page_user(self):
        index_html = self.get_index_page()
        if not index_html:
            return
        BS = BeautifulSoup(index_html, "html.parser")
        user_a = BS.find_all("a", class_="author-link")  # 获取用户的a标签
        for a in user_a:
            if a:
                href = a.get('href')
                self.add_wait_user(href[(href.rindex('/')) + 1:])
            else:
                print("获取首页author-link失败，跳过")
                continue

    # 获取粉丝页面，接口信息
    def get_follower_page(self, name_url, offset=0, limit=20):
        user_page_url = 'https://www.zhihu.com/api/v4/members/' + str(
            name_url) + '/followers?include=data%5B*%5D.answer_count%2Carticles_count%2Cgender%2Cfollower_count%2Cis_followed%2Cis_following%2Cbadge%5B%3F(type%3Dbest_answerer)%5D.topics&offset=' + str(
            offset) + '&limit=' + str(limit)
        try:
            index_html = self.session.get(user_page_url, headers=self.headers, timeout=35)
        except Exception as err:
            # 出现异常重试
            print("失败name_url：" + str(name_url) + "获取页面失败，放弃该用户")
            print(err)
            traceback.print_exc()
            return None
        finally:
            self.save_cookie()
            pass
        return index_html.text

    # 分析粉丝接口获取用户的所有粉丝用户
    # @param follower_page get_follower_page()中获取到的页面，这里获取用户hash_id请求粉丝接口获取粉丝信息
    def get_all_follower(self, name_url):
        follower_api = self.get_follower_page(name_url)
        # 判断是否获取到页面
        if not follower_api:
            return

        try:
            data = json.loads(follower_api)
            # 获取关注者数量
            follower_num = int(data['paging']['totals'])
            is_end = bool(data['paging']['is_end'])
        except Exception as err:
            print(err)
            traceback.print_exc()
            print("获取关注者列表失败，放弃")
            return

        # 获取关注者列表
        per_page = 20
        # 开始获取所有的关注者 math.ceil(follower_num/20)*20
        for i in range(0, int(math.ceil(follower_num / per_page)) * per_page, per_page):
            try:
                follower_api = self.get_follower_page(name_url, i, per_page)
                data = json.loads(follower_api)
                is_end = bool(data['paging']['is_end'])

                for user in data['data']:
                    self.add_wait_user(user['url_token'])  # 保存到redis

                if is_end:
                    break
            except Exception as err:
                print("获取关注者列表失败，继续循环")
                print(err)
                continue
                pass

    # 获取正在关注api
    def get_following_page(self, name_url, offset=0, limit=20):
        user_page_url = 'https://www.zhihu.com/api/v4/members/' + str(
            name_url) + '/followees?include=data%5B*%5D.answer_count%2Carticles_count%2Cgender%2Cfollower_count%2Cis_followed%2Cis_following%2Cbadge%5B%3F(type%3Dbest_answerer)%5D.topics&offset=' + str(
            offset) + '&limit=' + str(limit)
        try:
            index_html = self.session.get(user_page_url, headers=self.headers, timeout=35)
        except Exception as err:
            # 出现异常重试
            print("失败name_url：" + str(name_url) + "获取页面失败，放弃该用户")
            print(err)
            traceback.print_exc()
            return None
        finally:
            self.save_cookie()
            pass
        return index_html.text

    # 获取正在关注列表
    def get_all_following(self, name_url):
        following_api = self.get_following_page(name_url)
        # 判断是否获取到页面
        if not following_api:
            return

        try:
            data = json.loads(following_api)
            # 获取关注者数量
            following_num = int(data['paging']['totals'])
            is_end = bool(data['paging']['is_end'])
        except Exception as err:
            print(err)
            traceback.print_exc()
            print("获取关注者列表失败，放弃")
            return

        # 获取关注者列表
        per_page = 20
        # 开始获取所有的关注者 math.ceil(follower_num/20)*20
        for i in range(0, int(math.ceil(following_num / per_page)) * per_page, per_page):
            try:
                following_api = self.get_following_page(name_url, i, per_page)
                data = json.loads(following_api)
                is_end = bool(data['paging']['is_end'])

                for user in data['data']:
                    self.add_wait_user(user['url_token'])  # 保存到redis

                if is_end:
                    break
            except Exception as err:
                print("获取关注者列表失败，继续循环")
                print(err)
                continue
                pass

    # 加入带抓取用户队列，先用redis判断是否已被抓取过
    def add_wait_user(self, name_url):
        # 判断是否已抓取
        if not self.redis_con.hexists('already_get_user', name_url):
            self.counter += 1
            print(name_url + " 加入队列")
            self.redis_con.hset('already_get_user', name_url, 1)
            self.redis_con.lpush('user_queue', name_url)
            print("添加用户 " + name_url + "到队列")

    # 获取页面出错移出redis
    def del_already_user(self, name_url):
        self.threadLock.acquire()
        if not self.redis_con.hexists('already_get_user', name_url):
            self.counter -= 1
            self.redis_con.hdel('already_get_user', name_url)
        self.threadLock.release()

    # 获取单个用户详情页面
    def get_user_page(self, name_url):
        user_page_url = 'https://www.zhihu.com/api/v4/members/' + str(
            name_url) + '?include=locations%2Cemployments%2Cgender%2Ceducations%2Cbusiness%2Cvoteup_count%2Cthanked_Count%2Cfollower_count%2Cfollowing_count%2Ccover_url%2Cfollowing_topic_count%2Cfollowing_question_count%2Cfollowing_favlists_count%2Cfollowing_columns_count%2Cavatar_hue%2Canswer_count%2Carticles_count%2Cpins_count%2Cquestion_count%2Ccommercial_question_count%2Cfavorite_count%2Cfavorited_count%2Clogs_count%2Cmarked_answers_count%2Cmarked_answers_text%2Cmessage_thread_token%2Caccount_status%2Cis_active%2Cis_force_renamed%2Cis_bind_sina%2Csina_weibo_url%2Csina_weibo_name%2Cshow_sina_weibo%2Cis_blocking%2Cis_blocked%2Cis_following%2Cis_followed%2Cmutual_followees_count%2Cvote_to_count%2Cvote_from_count%2Cthank_to_count%2Cthank_from_count%2Cthanked_count%2Cdescription%2Chosted_live_count%2Cparticipated_live_count%2Callow_message%2Cindustry_category%2Corg_name%2Corg_homepage%2Cbadge%5B%3F(type%3Dbest_answerer)%5D.topics'
        try:
            index_html = self.session.get(user_page_url, headers=self.headers, timeout=35)
        except Exception as err:
            # 出现异常重试
            print("失败name_url：" + str(name_url) + "获取页面失败，放弃该用户")
            print(err)
            traceback.print_exc()
            return None
        finally:
            self.save_cookie()
            pass
        return index_html.text

    # 分析about页面，获取用户详细资料
    def get_user_info(self, name_url):
        about_user_api = self.get_user_page(name_url)
        # 判断是否获取到页面
        if not about_user_api:
            print("获取用户详情页面失败，跳过，name_url：" + name_url)
            return

        # 减慢爬虫速度
        time.sleep(self.sleep_time)
        # 获取页面的具体数据
        try:
            user_info = json.loads(about_user_api)

            nickname = user_info['name'] if 'name' in user_info else ''
            user_type = user_info['type'] if 'type' in user_info else 'people'
            self_domain = user_type + '/' + user_info['url_token']  # 个性域名
            gender = int(user_info['gender']) if 'gender' in user_info else -1  # 性别
            follower_num = int(user_info['following_count']) if 'following_count' in user_info else 0  # 粉丝
            following_num = int(user_info['follower_count'])  # 关注
            agree_num = int(user_info['voteup_count'])  # 赞同
            appreciate_num = int(user_info['thanked_count'])  # 感谢
            star_num = int(user_info['favorited_count'])  # 收藏
            # share_num = int(re.findall(r'<strong>(.*)</strong>.*分享', about_page)[0])
            share_num = 0  # 知乎个人首页改版，这里暂时没有数据可以抓了
            # browse_num = int(BS.find_all("span", class_="zg-gray-normal")[6].find("strong").get_text())
            browse_num = 0  # 知乎个人首页改版，这里暂时没有数据可以抓了
            trade = user_info['business']['name'] if 'business' in user_info else ''
            company = user_info['employments'][0]['company']['name'] if len(user_info['employments']) > 0 and 'company' in user_info['employments'][0]  else ''
            school = user_info['educations'][0]['school']['name'] if len(user_info['educations']) > 0 and 'school' in user_info['educations'][0]  else ''
            major = user_info['educations'][0]['major']['name'] if len(user_info['educations']) > 0 and 'major' in user_info['educations'][0] else ''
            job = user_info['employments'][0]['job']['name'] if len(user_info['employments']) > 0 and 'job' in user_info['employments'][0] else ''
            location = user_info['locations'][0]['name'] if len(user_info['locations']) > 0 else ''
            description = user_info['description'] if 'description' in user_info else ''
            ask_num = int(user_info['question_count'])
            answer_num = int(user_info['answer_count'])
            article_num = int(user_info['articles_count'])
            collect_num = int(user_info['favorite_count'])
            public_edit_num = int(user_info['logs_count'])

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
            print(user_info)
            print("获取数据出错，跳过用户")
            self.redis_con.hdel("already_get_user", name_url)
            self.del_already_user(name_url)
            print(err)
            traceback.print_exc()
            pass

    def save_cookie(self):
        self.session.cookies.save()

    def set_random_ua(self):
        length = len(self.ua)
        rand = random.randint(0, length - 1)
        self.headers['User-Agent'] = self.ua[rand]

    # 开始抓取用户，程序总入口
    def entrance(self):
        while 1:
            if int(self.redis_con.llen("user_queue")) <= 5:
                self.get_index_page_user()
            else:
                # 出队列获取用户name_url redis取出的是byte，要decode成utf-8
                name_url = str(self.redis_con.rpop("user_queue").decode('utf-8'))
                print("正在处理name_url：" + name_url)
                self.get_user_info(name_url)
                if int(self.redis_con.llen("user_queue")) <= int(self.max_queue_len):
                    self.get_all_follower(name_url)
                    self.get_all_following(name_url)
            self.set_random_ua()
            self.save_cookie()

    def run(self):
        print(self.name + " is running")
        self.entrance()

if __name__ == '__main__':
    # master代码不再需要登陆
    # login = GetUser(999, "登陆线程")

    threads = []
    threads_num = int(cfg.get("sys", "thread_num"))
    for i in range(0, threads_num):
        m = GetUser(i, "thread" + str(i))
        threads.append(m)

    for i in range(0, threads_num):
        threads[i].start()

    for i in range(0, threads_num):
        threads[i].join()
