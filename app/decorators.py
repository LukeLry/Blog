# -*- coding: utf-8 -*-
from functools import wraps
from flask import abort
from flask_login import current_user
from .models import Permission

#Python装饰器（decorator）在实现的时候被装饰后的函数其实已经是另外一个函数了（函数名等函数属性会发生改变）
#functools包中提供了一个叫wraps的decorator来消除这样的副作用。
#过滤未登陆用户的装饰器  装饰器本质是返回函数的函数
#当前用户被保存在g.user当中 如果么有用户登陆 g.user会是None:
"""
from functools import wraps
from flask import g, request, redirect, url_for

def login_required(f):
    #装饰器的嵌套 带参数的装饰器
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if g.user is None:
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function
"""
#检查用户权限的自定义修饰器
def permission_required(permission):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args,**kwargs):
            if not current_user.can(permission):
                abort(403)
            return f(*args,**kwargs)
        return decorated_function
    return decorator

#装饰器的嵌套#Python装饰器（decorator）在实现的时候被装饰后的函数其实已经是另外一个函数了（函数名等函数属性会发生改变）
#functools包中提供了一个叫wraps的decorator来消除这样的副作用。
#过滤未登陆用户的装饰器  装饰器本质是返回函数的函数
#当前用户被保存在g.user当中 如果么有用户登陆 g.user会是None:
"""
from functools import wraps
from flask import g, request, redirect, url_for

def login_required(f):
    #装饰器的嵌套 带参数的装饰器
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if g.user is None:
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function
"""
def admin_required(f):
    return permission_required(Permission.ADMINISTER)(f)