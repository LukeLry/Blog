# -*- encoding=UTF-8 -*-
from flask import url_for
import unittest
import json
import re
from base64 import b64encode
from app import create_app, db
from app.models import User, Role, Post, Comment

class APITestCase(unittest.TestCase):

    def setUp(self):
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        Role.insert_roles()
        self.client = self.app.test_client()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    #每一个请求都需要一个首部
    def get_api_headers(self, username, password):
        return {
            'Authorization': 'Basic ' + b64encode((username + ':' + password).encode('utf-8')).decode('utf-8'),
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }

    #这里返回错误码200??
    def test_no_auth(self):
        response = self.client.get(url_for('api.get_posts'),content_type='application/json')
        self.assertEqual(response.status_code, 401)
    """
    
    #测试错误的URL
    def test_404(self):
        response = self.client.get('/wrong/url',headers=self.get_api_headers('email', 'password'))
        self.assertEqual(response.status_code, 404)
        json_response = json.loads(response.get_data(as_text=True))
        self.assertEqual(json_response['error'], u'未找到')

    #测试错误的认证
    def test_bad_auth(self):
        # add a user
        r = Role.query.filter_by(name=u'用户').first()
        self.assertIsNotNone(r)
        u = User(email='18810326397@163.com', password='cat', confirmed=True,role=r)
        db.session.add(u)
        db.session.commit()

        #用错误密码进行验证
        response = self.client.get('/api/v1.0/posts/',headers=self.get_api_headers('18810326397@163.com', 'dog'))

        self.assertEqual(response.status_code, 401)

    def test_token_auth(self):
        #添加一个用户
        r = Role.query.filter_by(name=u'用户').first()
        self.assertIsNotNone(r)
        u = User(email='18810326397@163.com', password='cat', confirmed=True,role=r)
        db.session.add(u)
        db.session.commit()

        #测试用一个错误token去验证
        response = self.client.get('/api/v1.0/posts/',headers=self.get_api_headers('bad-token', ''))
        self.assertEqual(response.status_code, 401)

        #用一个正确的username和password去提交请求 并从json中获得一个token
        response = self.client.post('/api/v1.0/token',headers=self.get_api_headers('18810326397@163.com', 'cat'))
        self.assertEqual(response.status_code, 200)
        json_response = json.loads(response.get_data(as_text=True))
        self.assertIsNotNone(json_response.get('token'))
        token = json_response['token']

        #使用正确的token值去获得post列表 返回状态码200
        response = self.client.get('/api/v1.0/posts/',headers=self.get_api_headers(token, ''))
        self.assertEqual(response.status_code, 200)

    #匿名用户登陆 返回401
    def test_anonymous(self):
        response = self.client.get('/api/v1.0/posts/',headers=self.get_api_headers('', ''))
        self.assertEqual(response.status_code, 401)

    def test_unconfirmed_account(self):
        #添加一个没有确认的账户
        r = Role.query.filter_by(name=u'用户').first()
        self.assertIsNotNone(r)
        u = User(email='18810326397@163.com', password='cat', confirmed=False,role=r)
        db.session.add(u)
        db.session.commit()

        #用一个未确认账户获得一个博客列表
        response = self.client.get('/api/v1.0/posts/',headers=self.get_api_headers('18810326397@163.com', 'cat'))
        #403 禁止
        self.assertEqual(response.status_code, 403)
    """

    def test_posts(self):
        #添加一个用户
        r = Role.query.filter_by(name=u'用户').first()
        self.assertIsNotNone(r)
        u = User(email='18810326397@163.com', password='cat', confirmed=True,role=r)
        db.session.add(u)
        db.session.commit()

        """
        #提交一篇空的博文
        response = self.client.post('/api/v1.0/posts/',headers=self.get_api_headers('18810326397@163.com', 'cat'),data=json.dumps({'body': ''}))
        self.assertEqual(response.status_code, 400)
        """

        #写一篇博文
        response = self.client.post(url_for('api.new_post'),headers=self.get_api_headers('18810326397@163.com', 'cat'),data=json.dumps({'body': 'body of the *blog* post'}))
        self.assertEqual(response.status_code, 201)
        url = response.headers.get('Location')
        self.assertIsNotNone(url)

        #获取刚刚发布的博文
        response = self.client.get(url,headers=self.get_api_headers('18810326397@163.com', 'cat'))
        self.assertEqual(response.status_code, 200)
        json_response = json.loads(response.data.decode('utf-8'))
        self.assertEqual(json_response['url'], url)
        self.assertEqual(json_response['body'], 'body of the *blog* post')
        self.assertEqual(json_response['body_html'],'<p>body of the <em>blog</em> post</p>')


        """
        # get the post from the user
        response = self.client.get('/api/v1/users/{}/posts/'.format(u.id),headers=self.get_api_headers('john@example.com', 'cat'))
        self.assertEqual(response.status_code, 200)
        json_response = json.loads(response.get_data(as_text=True))
        self.assertIsNotNone(json_response.get('posts'))
        self.assertEqual(json_response.get('count', 0), 1)
        self.assertEqual(json_response['posts'][0], json_post)

        # get the post from the user as a follower
        response = self.client.get('/api/v1/users/{}/timeline/'.format(u.id),headers=self.get_api_headers('john@example.com', 'cat'))
        self.assertEqual(response.status_code, 200)
        json_response = json.loads(response.get_data(as_text=True))
        self.assertIsNotNone(json_response.get('posts'))
        self.assertEqual(json_response.get('count', 0), 1)
        self.assertEqual(json_response['posts'][0], json_post)

        # edit post
        response = self.client.put(url,headers=self.get_api_headers('john@example.com', 'cat'),data=json.dumps({'body': 'updated body'}))
        self.assertEqual(response.status_code, 200)
        json_response = json.loads(response.get_data(as_text=True))
        self.assertEqual('http://localhost' + json_response['url'], url)
        self.assertEqual(json_response['body'], 'updated body')
        self.assertEqual(json_response['body_html'], '<p>updated body</p>')
        """
