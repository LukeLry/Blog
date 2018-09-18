# -*- encoding=UTF-8 -*-
from flask import Flask,render_template
from flask_bootstrap import Bootstrap
from flask_mail import Mail
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from config import config
from flask_login import LoginManager
from flask_pagedown import PageDown
from flask_migrate import Migrate,MigrateCommand


#初始化Flask-login扩展
login_manager=LoginManager()
#session_protection属性可以设置为None basic strong 以提供不同的安全等级防止用户会话遭到篡改
login_manager.session_protection="strong"
#设置登陆页面的端点
login_manager.login_view="auth.login"


bootstrap=Bootstrap()
moment=Moment()
db=SQLAlchemy()
mail = Mail()
pagedown=PageDown()


def create_app(config_name):
    app=Flask(__name__)

    #这里config_name默认的配置为开发环境
    #传入不同的参数 创建不同配置的应用
    #将配置导入该app
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)

    bootstrap.init_app(app)
    moment.init_app(app)
    db.init_app(app)
    mail.init_app(app)
    login_manager.init_app(app)
    pagedown.init_app(app)

    #导入主蓝本
    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint)

    # 导入认证蓝本
    # 参数url_prefix='/xxx'的意思是设置request.url中的url前缀 注册蓝本中定义的所有路由都会加上指定前缀
    # 即当request.url是以/admin或者/user的情况下才会通过注册的蓝图的视图方法处理请求并返回
    from .auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint,url_prefix="/auth")

    #WebService API接口蓝本
    from .api_1_0 import api as api_1_0_blueprint
    app.register_blueprint(api_1_0_blueprint,url_prefix='/api/v1.0')

    return app


