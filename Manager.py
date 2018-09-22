# -*- encoding=UTF-8 -*-
from flask_script import Manager,Shell
from app import create_app,db
from app.models import User,Role,Post,Follow
from flask_migrate import Migrate,MigrateCommand

app=create_app("default")

#Flask使用扩展的通用方法:把程序实例作为参数传给构造器 初始化主类的实例
manager=Manager(app)
migrate=Migrate(app,db)

#Flask-Script的Shell 其实就是一个加载了Flask应用上下文的交互式环境 通过shell可以像启动应用一样操作动态数据
#make_shell_context() 函数注册了程序 数据库实例和模型 这些对象能直接导入shell
#在Flask应用上下文中运行python shell
def make_shell_context():
    return dict(app=app,db=db,User=User,Role=Role,Post=Post,Follow=Follow)
manager.add_command("shell",Shell(make_context=make_shell_context))
#manager.add_command("shell",Shell())
manager.add_command("db",MigrateCommand)

@manager.command                                                #自定义命令 函数名即是命令
def init_database():
    db.drop_all()
    db.create_all()
    #将用户角色注册到数据库
    User.generate_fake()
    Post.generate_fake()
    User.add_self_follows()
    Role.insert_roles()

    #db.session.add(User(email="18810326397@163.com",username="Luke",password="cat",confirmed=True))

    db.session.commit()                                        #数据库事物的概

"""
import os
COV = None
if os.environ.get('FLASK_COVERAGE'):
    import coverage
    COV = coverage.coverage(branch=True, include='app/*')
    COV.start()
"""

@manager.command
def test(coverage=False):
    """
    if coverage and not os.environ.get('FLASK_COVERAGE'):
        import sys
        os.environ['FLASK_COVERAGE'] = '1'
        os.execvp(sys.executable, [sys.executable] + sys.argv)
    """

    import unittest
    tests = unittest.TestLoader().discover('tests')
    unittest.TextTestRunner(verbosity=2).run(tests)

    """"
    if COV:
        COV.stop()
        COV.save()
        print('Coverage Summary:')
        COV.report()
        basedir = os.path.abspath(os.path.dirname(__file__))
        covdir = os.path.join(basedir, 'tmp/coverage')
        COV.html_report(directory=covdir)
        print('HTML version: file://%s/index.html' % covdir)
        COV.erase()
    """

#请求分析器
@manager.command
def profile(length=25,profile_dir=None):
    from werkzeug.contrib.profiler import ProfilerMiddleware
    app.wsgi_app=ProfilerMiddleware(app.wsgi_app,restrictions=[length],profile_dir=profile_dir)
    app.run()

@manager.command
def deploy():
    from flask_migrate import upgrade
    from app.models import Role,User

    #把数据库迁移到最新修订的版本
    upgrade()

    #创建用户角色
    Role.insert_roles()

    #让所有用户都关注此用户
    User.add_self_follows()

if __name__=="__main__":
    manager.run()
    #app.run(debug=True,threaded=True)