import http.cookiejar as cookielib
import sys
import os.path
import requests
from PIL import Image
from bs4 import BeautifulSoup
import time
import re


class Login:
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
    __xsrf = ''
    __cookie_file = ''
    __session = ''
    username = ''
    password = ''

    def __init__(self):

        self.__cookie_file = os.path.join(sys.path[0], 'cookie')  # cookie路径

        # session
        self.__session = requests.Session()
        self.__session.cookies = cookielib.LWPCookieJar(filename='cookie')
        try:
            self.__session.cookies.load(ignore_discard=True)
        except:
            print("Cookie 未能加载")
        finally:
            pass

    # 获取xsrf
    def get_xsrf(self):
        index_url = 'http://www.zhihu.com'
        # 获取登录时需要用到的_xsrf
        try:
            index_page = self.__session.get(index_url, headers=self.headers)
        except:
            print('获取知乎页面失败，请检查网络连接')
            sys.exit()
        html = index_page.text
        # 这里的_xsrf 返回的是一个list
        BS = BeautifulSoup(html, 'html.parser')
        self.__xsrf = BS.find(attrs={'name': '_xsrf'})
        # return self.__xsrf[0]
        return self.__xsrf

    # 获取验证码
    def get_captcha(self):
        t = str(time.time() * 1000)
        captcha_url = 'http://www.zhihu.com/captcha.gif?r=' + t + "&type=login"
        r = self.__session.get(captcha_url, headers=self.headers)
        with open('captcha.jpg', 'wb') as f:
            f.write(r.content)
            f.close()
            # 用pillow 的 Image 显示验证码
            # 如果没有安装 pillow 到源代码所在的目录去找到验证码然后手动输入
        try:
            im = Image.open('captcha.jpg')
            im.show()
            im.close()
        except:
            print(u'请到 %s 目录找到captcha.jpg 手动输入' % os.path.abspath('captcha.jpg'))
            sys.exit()
        captcha = input("请输入验证码\n>")
        return captcha

    # 验证是否登陆
    def check_login(self):
        check_url = 'https://www.zhihu.com/settings/profile'
        login_check = self.__session.get(check_url, headers=self.headers)
        print("验证登陆的http status code为：" + str(login_check.status_code))
        if int(x=login_check.status_code) == 200:
            return True
        else:
            return False

    # 进行模拟登陆
    def do_login(self, username, password):
        self.username = username
        self.password = password

        if re.match(r"^1\d{10}$", self.username):
            print("手机登陆\n")
            post_url = 'http://www.zhihu.com/login/phone_num'
            postdata = {
                '_xsrf': self.get_xsrf(),
                'password': self.password,
                'remember_me': 'true',
                'phone_num': self.username,
            }
        else:
            print("邮箱登陆\n")
            post_url = 'http://www.zhihu.com/login/email'
            postdata = {
                '_xsrf': self.get_xsrf(),
                'password': self.password,
                'remember_me': 'true',
                'email': self.username,
            }

        try:
            login_page = self.__session.post(post_url, postdata, headers=self.headers)
            print(login_page.status_code)
            print(str(login_page.text.encode('UTF-8')))
        except:
            postdata['captcha'] = self.get_captcha()
            login_page = self.__session.post(post_url, postdata, headers=self.headers)
            login_code = eval(login_page.text)
            print(str(login_code['msg'].encode('UTF-8')))
        # 保存登陆cookie
        self.__session.cookies.save()
