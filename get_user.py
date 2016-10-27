# -*- coding: utf-8 -*-
import login.login
import requests
import http.cookiejar as cookielib
import configparser
from bs4 import BeautifulSoup
import os
import redis
import json
import math
import re

class GetUser:
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
    }
    retry = 0  # 重试次数
    redis_con = ''
    counter = 0  # 被抓取用户计数
    xsrf = ''

    def __init__(self):
        # 获取配置
        self.config = configparser.ConfigParser()
        self.config.read("config.ini")

        # session
        self.session = session = requests.Session()
        self.session.cookies = cookielib.LWPCookieJar(filename='cookie')
        try:
            self.session.cookies.load(ignore_discard=True)
        except:
            print('Cookie 未能加载')
        finally:
            pass

        # 创建login对象
        lo = login.login.Login(self.session)
        '''
        # 模拟登陆
        if lo.check_login():
            print('您已经登录')
        else:
            # username = input('请输入你的用户名\n>  ')
            # password = input("请输入你的密码\n>  ")

            if self.config.get("zhihu_account", "username") and self.config.get("zhihu_account", "username"):
                username = self.config.get("zhihu_account", "username")
                password = self.config.get("zhihu_account", "password")
            else:
                username = input('请输入你的用户名\n>  ')
                password = input("请输入你的密码\n>  ")

            lo.do_login(username, password)
        '''
        # 初始化redis连接
        try:
            self.redis_con = redis.Redis(host=self.config.get("redis", "host"), port=self.config.get("redis", "port"),
                                         db=0)
        except:
            print("请安装redis")
            os.exit()

    # 获取首页html
    def get_index_page(self):
        index_url = 'https://www.zhihu.com/'
        try:
            index_html = self.session.get(index_url, headers=self.headers)
        except:
            # 出现异常重试
            if self.retry < self.config.get("sys", "retry_times"):
                print("获取页面失败，正在重试......")
                self.retry += 1
                return self.get_index_page()
            else:
                return None
        finally:
            self.retry = 0
        return index_html.text

    # 获取单个用户页面
    def get_user_page(self, name_url):
        user_page_url = 'https://www.zhihu.com' + str(name_url) + '/about'
        try:
            index_html = self.session.get(user_page_url, headers=self.headers)
        except:
            # 出现异常重试
            if self.retry < int(self.config.get("sys", "retry_times")):
                print("获取页面失败，正在重试......")
                self.retry += 1
                return self.get_user_page(name_url)
            else:
                return None
        finally:
            self.retry = 0
        return index_html.text

    # 获取粉丝页面
    def get_follower_page(self, name_url):
        user_page_url = 'https://www.zhihu.com' + str(name_url) + '/followers'
        try:
            index_html = self.session.get(user_page_url, headers=self.headers)
        except:
            # 出现异常重试
            if self.retry < int(self.config.get("sys", "retry_times")):
                print("获取页面失败，正在重试......")
                self.retry += 1
                return self.get_follower_page(name_url)
            else:
                return None
        finally:
            self.retry = 0
        return index_html.text

    def get_following_page(self, name_url):
        user_page_url = 'https://www.zhihu.com' + str(name_url) + '/followers'
        try:
            index_html = self.session.get(user_page_url, headers=self.headers)
        except:
            # 出现异常重试
            if self.retry < int(self.config.get("sys", "retry_times")):
                print("获取页面失败，正在重试......")
                self.retry += 1
                return self.get_follower_page(name_url)
            else:
                return None
        finally:
            self.retry = 0
        return index_html.text

    # 获取首页上的用户列表，存入redis
    def get_index_page_user(self):
        index_html = self.get_index_page()
        BS = BeautifulSoup(index_html, "html.parser")
        user_a = BS.find_all("a", class_="author-link")  # 获取用户的a标签
        for a in user_a:
            if a:
                self.add_wait_user(a.get('href'))
            else:
                continue

    # 加入带抓取用户队列，先用redis判断是否已被抓取过
    def add_wait_user(self, name_url):
        # 判断是否已抓取
        if not self.redis_con.hexists('already_get_user', name_url):
            print(name_url + " 加入队列")
            self.redis_con.hset('already_get_user', name_url, 1)
            self.redis_con.lpush('user_queue', name_url)
            print("添加用户 " + name_url + "到队列")
            return True
        else:
            return False

    # 分析粉丝页面获取用户的所有粉丝用户
    # @param follower_page get_follower_page()中获取到的页面，这里获取用户hash_id请求粉丝接口获取粉丝信息
    def get_all_follower(self, follower_page):
        BS = BeautifulSoup(follower_page, 'html.parser')
        # 获取关注者数量
        follower_num = int(BS.find('span', text='关注者').find_parent().find('strong').get_text())
        # 获取用户的hash_id
        hash_id = json.loads(BS.select("#zh-profile-follows-list")[0].select(".zh-general-list")[0].get('data-init'))['params']['hash_id']

        # 获取关注者列表
        self.get_xsrf(follower_page)  # 获取xsrf
        post_url = 'https://www.zhihu.com/node/ProfileFollowersListV2'
        # 开始获取所有的关注者 math.ceil(follower_num/20)*20
        for i in range(0, math.ceil(follower_num/20)*20, 20):
            post_data = {
                'method': 'next',
                'params': json.dumps({"offset": i, "order_by": "created", "hash_id": hash_id})
            }
            try:
                j = self.session.post(post_url, params=post_data, headers=self.headers).text.encode('latin-1').decode('unicode-escape')
                pattern = re.compile(r"class=\"zm-item-link-avatar\"[^\"]*\"([^\"]*)", re.DOTALL)
                j = pattern.findall(j)
                for user in j:
                    user = user.replace('\\', '')
                    self.add_wait_user(user)  # 保存到redis
            except:
                print("获取正在关注失败")
                pass

    # 获取正在关注列表
    def get_all_following(self, following_page):
        BS = BeautifulSoup(following_page, 'html.parser')
        # 获取关注者数量
        following_num = int(BS.find('span', text='关注了').find_parent().find('strong').get_text())
        # 获取用户的hash_id
        hash_id = json.loads(BS.select("#zh-profile-follows-list")[0].select(".zh-general-list")[0].get('data-init'))['params']['hash_id']

        # 获取关注者列表
        self.get_xsrf(following_page)  # 获取xsrf
        post_url = 'https://www.zhihu.com/node/ProfileFolloweesListV2'
        # 开始获取所有的关注者 math.ceil(follower_num/20)*20
        for i in range(0, math.ceil(following_num/20)*20, 20):
            post_data = {
                'method': 'next',
                'params': json.dumps({"offset": i, "order_by": "created", "hash_id": hash_id})
            }
            try:
                j = self.session.post(post_url, params=post_data, headers=self.headers).text.encode('latin-1').decode('unicode-escape')
                pattern = re.compile(r"class=\"zm-item-link-avatar\"[^\"]*\"([^\"]*)", re.DOTALL)
                j = pattern.findall(j)
                for user in j:
                    user = user.replace('\\', '')
                    self.add_wait_user(user)  # 保存到redis
            except:
                print("获取正在关注失败")
                pass

    # 分析about页面，获取用户详细资料
    def get_user_info(self, name_url, about_page):
        BS = BeautifulSoup(about_page, 'html.parser')
        # 获取关注者数量
        follower_num = int(BS.find('span', text='关注者').find_parent().find('strong').get_text())
        following_num = int(BS.find('span', text='关注了').find_parent().find('strong').get_text())

    # 获取xsrf保存到header
    def get_xsrf(self, html):
        BS = BeautifulSoup(html, 'html.parser')
        xsrf_input = BS.find("input", attrs={'name': '_xsrf'})
        self.xsrf = xsrf_input.get("value")
        self.headers['X-Xsrftoken'] = self.xsrf
        self.session.cookies.save()
        print("获取到xsrf：" + self.xsrf)

if __name__ == '__main__':
    gu = GetUser()
    follower_page = '''

    '''

    follower_page = (gu.get_follower_page('/org/teng-xun-ke-ji'))
    gu.get_all_following(follower_page)
