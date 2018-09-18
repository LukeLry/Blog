# -*- encoding=UTF-8 -*-
from flask import jsonify
from app.exceptions import ValidationError
from . import api

def bad_request(message):
    response = jsonify({'error': u'坏请求', 'message': message})
    response.status_code = 400
    return response


def unauthorized(message):
    response = jsonify({'error': u'未授权', 'message': message})
    response.status_code = 401
    return response


def forbidden(message):
    response = jsonify({'error': u'禁止', 'message': message})
    response.status_code = 403
    return response


#只有当处理API蓝本中的路由时抛出异常才会调用这个程序？？？
@api.errorhandler(ValidationError)
def validation_error(e):
    return bad_request(e.args[0])
