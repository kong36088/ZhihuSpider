import login.login

lo = login.login.Login()

if lo.check_login():
    print('您已经登录')
else:
    username = input('请输入你的用户名\n>  ')
    password = input("请输入你的密码\n>  ")
    # lo.do_login('13527886582', '272138127')
    lo.do_login(username, password)
