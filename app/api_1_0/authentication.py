# -*- coding: utf-8 -*-
from ..models import User,AnonymousUser
from flask_httpauth import HTTPBasicAuth
from .errors import unauthorized,forbidden
from flask import jsonify,g
from .import api
#该用户认证的方法只在API蓝本中使用 Flask-HTTPAuth扩展只在蓝本包中初始化
auth=HTTPBasicAuth()

#使用Flask-HTTPAuth认证用户
#由于REST的无状态 即服务器在两次请求之间不能记住客户端的任何信息
#客户端必须在发出的请求中包含所有必要信息 因此所有请求都必须包含密令
#Flask-Login将会话保存在客户端cookie中 但REST Web服务中还存在除浏览器以外的客户端 所以使用cookie不现实

#Flask-HTTPAuth提供了一个便利的包装 将HTTP认证协议隐藏在装饰器中
#用户密令包含在请求的Authorization首部中
#做Http Basic Authentication验证 将验证过用户数据存储在g中 方便在其他路由函数使用
#接收HTTP首部Authorization字段中 username和password的base64加密后的编码 解密后得到password username
#验证所需信息username password 在回调函数中提供
#每次访问REST API的时候 verify_password会被自动执行
@auth.verify_password
def verity_password(email_or_token,password):
    #若该参数为空 则为匿名用户
    if email_or_token=='':
        g.current_user=AnonymousUser()
        return True
    #如果password为空 则认为email_or_token参数提供的是令牌 按照令牌的方式进行认证
    if password=='':
        #return User.query.get(data['id'])
        g.current_user=User.verify_auth_token(email_or_token)
        g.token_used=True
        return g.current_user is not None
    #如果两个参数都不为空 假定使用常规的邮件地址和密码进行认证 传递的虽然是经过base64加密的password 但并不安全
    #是否使用令牌的认证是可选的 取决于客户端请求Authorization字段中是否包含用户名和密码的base64加密字符串 是否存在token
    user=User.query.filter_by(email=email_or_token).first()
    if not user:
        return False
    g.current_user=user
    g.token_used=False
    return user.verify_password(password)

#客户端通过此路由获得自己的token值
@api.route('/token')
def get_token():
    #不能带着token申请token
    if g.current_user.is_anonymous() or g.token_used:
        return unauthorized(u'没有登陆或者已经申请了令牌')
    return jsonify({'token':g.current_user.generate_auth_token(expiration=3600),'expiration':3600})

#如果认证密令不正确 当verity_password认证失败返回False 服务器向客户端返回401错误 自动调用auth_error
#该细节隐藏在@auth.error_handler装饰器中
#默认状态下Flask-HTTPAuthzidong 生成这个状态码
#自定义该错误响应和API返回的其他错误保持一致
@auth.error_handler
def auth_error():
    return unauthorized(u'HTTP认证失败')

#利用请求钩子 过滤登陆但木有确认的用户
#g用来传递上下文数据 g提供了一个方法将数据共享到路由函数里面区
#before_request请求钩子仅仅能在该蓝本中使用 与before_app_request钩子区别开
@api.before_request
@auth.login_required
def before_request():
    if not g.current_user.is_anonymous() and not g.current_user.confirmed:
        return forbidden(u'该账户没有确认')


