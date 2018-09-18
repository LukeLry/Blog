# -*- encoding=UTF-8 -*-

import unittest
from flask import current_app,url_for
from app import create_app
from app import create_app,db

class BasicsTestCase(unittest.TestCase):
    #创建测试环境 使用测试配置创建程序 然后激活上下文 确保在测试中使用current_app
    def Setup(self):
        self.app = create_app('testing')
        #创建应用上下文
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

    #清除数据库和程序上下文
    def teardown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    #当前应用是否存在
    def test_app_exits(self):
        self.assertFalse(current_app is None)

    #当前是否是测试环境
    def test_app_is_testing(self):
        self.assertFalse(current_app.config['TESTING'])

