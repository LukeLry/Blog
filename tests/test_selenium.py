# -*- encoding=UTF-8 -*-

import unittest
from flask import current_app, url_for, json
from app import create_app, db
from selenium import webdriver
import threading
import re
from app.models import User,Role,Post

#Selenium测试存在一个utf-8编码的问题
"""
class SeleniumTestCase(unittest.TestCase):
    client = None

    #cls是一个上下文环境类
    @classmethod
    def setUpClass(cls):
        # 启动火狐浏览器
        try:
            #通过webdriver.Firefox()获取到了Firefox()浏览器对象
            cls.client = webdriver.Firefox()
        except:
            pass

        if cls.client:
            #创建一个Flask应用 使用测试环境的配置
            cls.app = create_app('testing')
            cls.app_context = cls.app.app_context()
            cls.app_context.push()
            db.create_all()

            #禁止日志 保持输出简洁  ???
            import logging
            logger=logging.getLogger('werkzeug')
            logger.setLevel("ERROR")

            #创建数据库 并使用一些虚拟数据填充
            db.create_all()
            Role.insert_roles()
            User.generate_fake(10)
            Post.generate_fake(10)

            #添加管理员
            admin_role=Role.query.filter_by(permissions=0xff).first()
            admin=User(email='18810326397@163.com',username='Luke',password='cat',role=admin_role,confirmed=True)
            db.session.add(admin)
            db.session.commit()

            #在一个线程中启动Flask服务器
            threading.Thread(target=cls.app.run).start()


    @classmethod
    def tearDownClass(cls):
        if cls.client:
            #给服务器发送一个HTTP请求 找到对应视图函数关闭服务器
            cls.client.get('http://localhost:5000/shutdown')

            #关闭浏览器
            cls.client.close()

            #销毁数据库
            db.drop_all()
            db.session.remove()

            #删除程序上下文
            cls.app_context.pop()


    def setUp(self):
        if not self.client:
            self.skipTest(u'火狐浏览器不可用')

    def tearDown(self):
        pass


    def test_admin_home_page(self):
        # 进入首页测试
        self.client.get('http://localhost:5000/')
        self.assertTrue(re.search(u'主页', self.client.page_source))

        #进入登陆页面
        self.client.find_element_by_link_text(u"登入").click()
        self.assertTrue(u'登入' in self.client.page_source)

        #登陆
        self.client.find_element_by_name(u'邮箱').send_keys('18810326397@163.com')
        self.client.find_element_by_name(u'密码').send_keys('cat')
        self.client.find_element_by_name(u'提交').click()
        self.assertTrue(re.search(u'你好',self.client.page_source))

        #进入用户个人资料页面
        self.client.find_elements_by_link_text(u'个人资料').click()
        self.assertTrue('Luke' in self.client.page_source)

"""


