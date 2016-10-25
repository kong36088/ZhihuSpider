import login.login
import requests
import http.cookiejar as cookielib


class GetUser:
    session = ''

    def __init__(self):
        # session
        self.session = session = requests.Session()
        self.session.cookies = cookielib.LWPCookieJar(filename='cookie')
        try:
            self.session.cookies.load(ignore_discard=True)
        except:
            print("Cookie 未能加载")
        finally:
            pass

        lo = login.login.Login(self.session)

        # 模拟登陆
        if lo.check_login():
            print('您已经登录')
        else:
            # username = input('请输入你的用户名\n>  ')
            # password = input("请输入你的密码\n>  ")
            lo.do_login('13527886582', '272138127')
            # lo.do_login(username, password)

