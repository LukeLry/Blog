# -*- encoding=UTF-8 -*-
from flask import render_template,redirect,request,url_for,flash
from flask_login import login_user,logout_user,login_required,current_user
#导入认证蓝本
from . import auth
from ..models import User
from .forms import LoginForm,RegistrationForm,ChangePasswordForm,PasswordResetRequestForm,PasswordResetForm
from app import db
from ..email import send_email
from flask import current_app

@auth.route("/login",methods=["GET","POST"])
def login():
    form=LoginForm()
    #提交表单后，如果数据能被所有验证函数接受,validate_on_sumbmit()返回true
    if form.validate_on_submit():                                   #验证表单数据
        user=User.query.filter_by(email=form.email.data).first()
        if user is not None and user.verify_password(form.password.data):
            #登入该用户
            login_user(user,form.remember_me.data)
            #Flask-Login会把源地址保存在查询字符串的next参数中
            return redirect(request.args.get("next") or url_for("main.index"))
        #若用户输入的电子邮件或者密码不正确，程序会设定一个Flash消息，再次渲染表单，让用户重新登陆
        flash(u"用户名或密码错误")
    return render_template("auth/login.html",form=form)

@auth.route("/logout")
@login_required
def logout():
    #登出当前用户
    logout_user()
    flash(u"你已经登出")
    return redirect(url_for("main.index"))

@auth.route("/register",methods=["GET","POST"])
def register():
    form=RegistrationForm()
    if form.validate_on_submit():
        user=User(email=form.email.data,username=form.username.data,password=form.password.data)

        #通过配置 程序已经可以可以在请求末尾自动提交数据库变化
        #这里要提交数据库之后才能赋予新用户的ID值 确认令牌需要用到Id 所以不能延后提交
        db.session.add(user)
        db.session.commit()
        #产生用户认证token 用于短信验证
        token=user.generate_confirmation_token()

        #账户确认
        send_email(user.email,u"请确认你的账户","auth/email/confirm",user=user,token=token)


        flash(u"一封电子邮件已经发至你的邮箱")
        return redirect(url_for("main.index"))
    return render_template("auth/register.html",form=form)

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

@auth.route("/confirm/<token>")
@login_required                                       #路由保护 确保用户先登陆
def confirm(token):
    if current_user.confirmed:                        #避免用户多次点击确认令牌
        return redirect(url_for("main.index"))
    if current_user.confirm(token):
        flash(u"你已经确认了你的账户")
    else:
        flash(u"确认连接已经过期失效")
    return redirect(url_for("main.index"))

#对蓝本来说 before_request钩子只能应用到属于蓝本的请求上
#若想在蓝本中使用针对程序全局请求的钩子 必须使用before_app_request
#个人觉得这里有个Bug 详情见幕布
@auth.before_app_request
def before_request():
    #处理任何请求前先要经过这个函数过滤
    if current_user.is_authenticated():
        current_user.ping()                              #更新用户最后登陆时间
        if not current_user.confirmed and request.endpoint[0:4]!="auth" and request.endpoint!="static":
            return redirect(url_for("auth.unconfirmed"))

#用户已经登陆
#用户的账户还没确认
#请求的端点不在认证蓝本中 重定向到auth/unconfirmed 如果认证的端点在认证蓝本中会出现循环重定向问题
#则重定向到尚未确认的页面

@auth.route("/unconfirmed")
def unconfirmed():
    if current_user.is_anonymous() or current_user.confirmed:
        return redirect(url_for("main.index"))
    return render_template("auth/unconfirmed.html")

#is_resend_coonfirmation=False

#该视图路由的URL链接写在auth/unconfirmed.html中
@auth.route("/resend_confirmation")
@login_required
def resend_confirmation():
    #is_resend_coonfirmation = True
    token=current_user.generate_confirmation_token()
    send_email(current_user.email,u"确认你的账户","auth/email/confirm",user=current_user,token=token)
    flash(u"一封新的确认邮件已经发给了你")
    return redirect(url_for("main.index"))

@auth.route("/change_password", methods=['GET', 'POST'])
@login_required  #只有登录的人才能修改密码
def change_password():
    form = ChangePasswordForm()
    if form.validate_on_submit():
        #验证旧的密码是否合法
        if current_user.verify_password(form.old_password.data):
            current_user.password = form.password.data
            #修改密码
            db.session.add(current_user)
            #加入数据库的session 这里不需要.commit() 在配置文件中已经配置了自动保存
            flash(u"你已经完成了密码修改")
            return redirect(url_for('main.index'))
        else:
            flash(u"无效密码")
    return render_template("auth/change_password.html", form=form)


#发送更改密码邮件的视图 忘记密码的处理
@auth.route("/password_reset_request",methods=['GET','POST'])
#html里的链接要写函数名
def password_reset_request():
    if not current_user.is_anonymous:
        #验证密码是否为登录状态 如果是 则终止重置密码
        return redirect(url_for('main.index'))

    form = PasswordResetRequestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            #如果用户存在
            token = user.generate_reset_password_token()
            #调用User模块中的generate_reset_token函数生成验证信息
            send_email(user.email,u'重置密码','auth/email/reset_password',
                        user=user,token=token,next=request.args.get('next'))
            #调用send_email函数 渲染邮件内容之后发送重置密码邮件
            flash(u'重置密码的邮件已经发送')
        return redirect(url_for('auth.login'))
    #reset_password.html是填写邮件的页面
    return render_template('auth/reset_password.html',form=form)

#更改密码的页面 从邮件中的链接进入
@auth.route('/password_reset/<token>', methods=['GET', 'POST'])
def password_reset(token):
    if not current_user.is_anonymous:
        # 验证密码是否为登录状态 如果是 则终止重置密码
        return redirect(url_for('main.index'))
    form = PasswordResetForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is None:
            return redirect(url_for('main.index'))
        if user.reset_password(token, form.newpassword.data):
            flash(u'你的密码已经被重置')
            return redirect(url_for('auth.login'))
        else:
            return redirect(url_for('main.index'))
    return render_template('auth/reset_password.html', form=form)