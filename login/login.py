import sys
import os.path
from PIL import Image
from bs4 import BeautifulSoup
import time
import re
import json


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
    __session = ''
    username = ''
    password = ''

    def __init__(self, session):
        self.__session = session

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
        xsrf_input = BS.find(attrs={'name': '_xsrf'})
        pattern = r'value=\"(.*?)\"'
        print(xsrf_input)
        self.__xsrf = re.findall(pattern, str(xsrf_input))
        return self.__xsrf[0]

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
        if int(login_check.status_code) == 200:
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
            login_text = json.loads(login_page.text.encode('latin-1').decode('unicode-escape'))
            print(login_text)
            # 需要输入验证码 r = 0为登陆成功代码
            if login_text['r'] == 1:
                sys.exit()
        except:
            postdata['captcha'] = self.get_captcha()
            login_page = self.__session.post(post_url, postdata, headers=self.headers)
            print(json.loads(login_page.text.encode('latin-1').decode('unicode-escape')))
        # 保存登陆cookie
        self.__session.cookies.save()
