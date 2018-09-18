# -*- encoding=UTF-8 -*-

import os
basedir=os.path.abspath(os.path.dirname(__file__))

class Config(object):                                                      #配置基类
    SECRET_KEY="Luke is a good boy"                                        #用于预防 CSRF
    SQLALCHEMY_COMMIT_ON_TEARDOWN=True                                     #该配置为True,则每次请求结束都会自动commit数据库的变动
    SQLALCHEMY_TRACK_MODIFICATIONS=True                                    #消除一条莫名的警告

    FLASKY_MAIL_SUBJECT_PREFIX  = "[Luke]"                                 # 邮件发送text的前缀
    FLASKY_MAIL_SENDER  = "347670374@qq.com"                               # 负责给注册用户发送邮件的邮箱

    FLASKY_ADMIN="18810326397@163.com"                                     #管理员邮箱

    #分页参数
    FLASKY_POSTS_PER_PAGE=10

    FLASKY_FOLLOWERS_PER_PAGE=10

    FLASKY_COMMENTS_PER_PAGE=10

    #处理SQL慢查询
    SQLALCHEMY_RECORD_QUERIES = True
    FLASKY_SLOW_DB_QUERY_TIME = 0.5

    #UPLOAD_FOLDER=os.getcwd()+"/app/static/avatar"

    @staticmethod
    #@classmethod
    def init_app(app):                                                     #使用对应配置初始化一个APP 暂时没用
        pass

class DevelopmentConfig(Config):
    DEBUG=True
    SQLALCHEMY_DATABASE_URI ="sqlite:///" + os.path.join(basedir,"data-dev.db")

    #邮件相关
    MAIL_SERVER = 'smtp.qq.com'                                             #电子邮件服务器的主机名或IP地址
    MAIL_PORT = 587
    MAIL_USE_TLS= True                                                      #启用传输层安全协议

    #SMTP服务器用户名
    MAIL_USERNAME = '347670374@qq.com'
    MAIL_PASSWORD = "qbszifbajbinbgea"                                      #QQ邮箱开通SMTP服务的授权码

class TestingConfig(Config):                                                #测试配置类 CSRF保护
    WTF_CSRF_ENABLED=False                                                  #测试的时候禁用CSRF保护?
    TESTING=True
    SQLALCHEMY_DATABASE_URI ="sqlite:///" + os.path.join(basedir,"data-test.db")

class ProductionConfig(Config):                                             #生产配置类
    SQLALCHEMY_DATABASE_URI ="sqlite:///" + os.path.join(basedir,"data.db")

    #在程序启动的过程中 Flask会创建一个python提供的logging.Logger类实例
    #并将其附属在程序实例上 得到app.logger
    #在调试模式中 日志记录器会把记录写入终端 在生产模式中 默认情况下没有配置日志处理程序 如果不添加处理程序 就不会保存日志
    #所有配置实例都有一个init_app()的方法 从Config中继承过来 在ProductionConfig中重写 在create_app()中调用
    #在ProductionConfig类的init_app()方法的实现中
    @classmethod
    def init_app(cls, app):
        Config.init_app(app)

        # email errors to the administrators
        import logging
        from logging.handlers import SMTPHandler
        credentials = None
        secure = None

        if getattr(cls, 'MAIL_USERNAME', None) is not None:
            credentials = (cls.MAIL_USERNAME, cls.MAIL_PASSWORD)
            if getattr(cls, 'MAIL_USE_TLS', None):
                secure = ()

        mail_handler = SMTPHandler(
            mailhost=(cls.MAIL_SERVER, cls.MAIL_PORT),
            fromaddr=cls.FLASKY_MAIL_SENDER,
            toaddrs=[cls.FLASKY_ADMIN],
            subject=cls.FLASKY_MAIL_SUBJECT_PREFIX + u'应用错误',
            credentials=credentials,
            secure=secure)
        #日志等级被设置为logging.ERROR 只有发生严重错误的时候才会发送电子邮件
        mail_handler.setLevel(logging.ERROR)

        app.logger.addHandler(mail_handler)



#config作为外部配置的接口

config={
    "development":DevelopmentConfig,
    "testing":TestingConfig,
    "production":ProductionConfig,
    "default":DevelopmentConfig
}