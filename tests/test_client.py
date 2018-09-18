# -*- encoding=UTF-8 -*-

import unittest
import re
from flask import current_app,url_for
from app import create_app
from app import create_app,db
from app.models import User,Role


#flask中的成员函数test_client()可以返回一个客户端对象，
#可以模拟Web客户端 用来同Web服务端进行交互 它可以测试Web程序 也可以用来测试Rest API，

class FlaskClientTest(unittest.TestCase):

    def setUp(self):
        self.app = create_app('testing')
        #创建测试用的应用上下文
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        Role.insert_roles()
        #该测试客户端可以使用cookie
        self.client = self.app.test_client(use_cookies=True)


    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    #测试主页
    def test_home_page(self):
        #get方法得到结果是FlaskResponse对象
        response = self.client.get(url_for('main.index'))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(u'主页' in response.get_data(as_text=True))

    #测试注册路由
    def test_register_login_logout(self):
        #注册新账户

        response = self.client.post(url_for('auth.register'), data={
            'email': '879651072@qq.com',
            'username': 'Hyman',
            'password': '123',
            'password2': '123'})

        #302 状状态码表示重定向
        self.assertTrue(response.status_code == 302)

        # 重置密码 这里有点问题没解决
        """
        response = self.client.post(url_for('auth.password_reset_request'), data={'email': '879651072@qq.com'})
        data = response.get_data(as_text=True)
        #self.assertTrue(u"重置密码的邮件已经发送" in data)
        self.assertTrue(u"登陆" in data)

        user = User.query.filter_by(email="879651072@qq.com").first()
        token = user.generate_reset_password_token()
        response = self.client.get(url_for("auth.password_reset", token=token,data={
            'email':'879651072@qq.com',
            'newpassword':'cat',
            'newpassword2':'cat'
        }), follow_redirects=True)

        data = response.get_data(as_text=True)
        self.assertTrue(u'你的密码已经被重置' in data)
        """


        #使用新的账户登录
        #指定follow_redirects=True后 返回的不是状态码302
        response=self.client.post(url_for("auth.login"),data={
            "email":"879651072@qq.com",
            "password":"123",                                #注意这里要使用重置后的密码
        },follow_redirects=True)

        data=response.get_data(as_text=True)

        self.assertTrue(re.search(u"你好,\s+Hyman",data))
        self.assertTrue(u"你还没有确认你的账户" in data)

        #发送确认令牌
        user=User.query.filter_by(email="879651072@qq.com").first()
        token=user.generate_confirmation_token()
        response=self.client.get(url_for("auth.confirm",token=token),follow_redirects=True)

        data=response.get_data(as_text=True)
        self.assertTrue(u"你已经确认了你的账户" in data)

        #修改密码
        response = self.client.post(url_for("auth.change_password"), data={
            "old_password": "123",
            "password": "456",
            "password2": "456",
        }, follow_redirects=True)

        data = response.get_data(as_text=True)
        self.assertTrue(u"你已经完成了密码修改" in data)




        #退出
        response=self.client.get(url_for("auth.logout"),follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        data=response.get_data(as_text=True)
        self.assertTrue(u"你已经登出" in data)
