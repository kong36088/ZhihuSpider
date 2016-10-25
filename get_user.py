import login.login
import requests
import http.cookiejar as cookielib
import configparser


class GetUser:
    session = ''
    config = ''

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
            print("Cookie 未能加载")
        finally:
            pass

        # 创建login对象
        lo = login.login.Login(self.session)

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

    def get_data(self):
        pass


if __name__ == '__main__':
    gu = GetUser()
    gu.get_data()
