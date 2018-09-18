# -*- coding: utf-8 -*-
from flask_mail import Mail, Message
from threading import Thread
from flask import current_app
from flask import Flask,render_template
from . import mail

"""
#异步发送电子邮件的装饰器
def async(f):
    def wrapper(*args, **kwargs):
        thr = Thread(target = f, args = args, kwargs = kwargs)
        thr.start()
    return wrapper
"""

#@async
def send_async_email(app,msg):
    """
        This function is a thread function. Each of these threads will send mail.
    """
    #with 事先产生上下文
    with app.app_context():
        mail.send(msg)


def send_email(receiver,subject,template,**kwargs):
    app=current_app._get_current_object()                  #关键问题 current_app只是当前应用的代理 current_app._get_current_object()获取真正当前应用的实例
    msg=Message(subject=subject,sender=app.config["FLASKY_MAIL_SENDER"],recipients=[receiver],charset="utf-8")
    msg.body=render_template(template+".txt",**kwargs)
    msg.html=render_template(template+".html",**kwargs)
    thr=Thread(target=send_async_email,args=[app,msg])     #每一封邮件都开一个线程 创建线程类
    thr.start()
    return thr


#许多Flask的扩展都是假定自己运行在一个活动的应用和请求上下文中
#Flask-Mail的send函数使用到current_app 这个上下文
#所以当 mail.send()函数在一个线程中执行的时候需要人为的创建一个上下文
#在示例 send_async_email 中使用了 app.app_context() 来创建一个上下文
