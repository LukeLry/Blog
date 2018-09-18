# -*- encoding=UTF-8 -*-
from flask import render_template,request,jsonify
from . import main

#404 500状态码由Flask自己生成 其他状态码由Web服务生成 在API蓝本中errors.py模块作为辅助函数实现
#如果使用errorhandler修饰器 只有蓝本中的错误才能触发处理程序
#要想注册程序全局的错误处理程序 必须使用app_errorhandler

@main.app_errorhandler(404)
def page_not_found(e):
    #在错误处理程序中根据客户端请求的格式改写响应 内容协商
    #检查Accept content-type 请求首部(Werkzeug将其解码为request.accept_mimetypes)
    #根据首部的值决定客户端期望接收的响应格式
    #浏览器一般不限制响应格式 只为接收JSON格式而不接受HTML格式的客户端生成JSON格式
    if request.accept_mimetypes.accept_json and not request.accept_mimetypes.accept_html:
        response=jsonify({'error':u'未找到'})
        response.status_code=404
        return response
    return render_template("404.html"),404

@main.app_errorhandler(500)
def internal_server_error(e):
    if request.accept_mimetypes.accept_json and not request.accept_mimetypes.accept_html:
        response=jsonify({'error':u'内部服务器错误'})
        response.status_code=500
        return response
    return render_template("500.html"),500

