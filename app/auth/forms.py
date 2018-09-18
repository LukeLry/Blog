# -*- encoding=UTF-8 -*-
from flask_wtf import FlaskForm
#FlaskForm基类由Flask-wtf定义 字段和验证函数可以直接从wt_forms包中导入
from wtforms import StringField,PasswordField,BooleanField,SubmitField
from wtforms.validators import DataRequired,Length,Email,Regexp,EqualTo
from wtforms import ValidationError
from ..models import User

class LoginForm(FlaskForm):
    email=StringField(u"邮箱",validators=[DataRequired(),Length(1,64),Email()])         #用电子邮件作为用户名
    password=PasswordField(u"密码",validators=[DataRequired()])
    #False 关闭浏览器后用户会话过期 True 在用户浏览器中写入一个长期的cookie 该cookie可以复现用会话
    remember_me=BooleanField(u"记住我")                                                 #复选框 true  or false 默认为true
    submit=SubmitField(u"登陆")                                                         #表单提交按钮

class RegistrationForm(FlaskForm):
    email=StringField(u"邮箱",validators=[DataRequired(),Length(1,64),Email()])

    username=StringField(u"用户名",validators=[DataRequired(),Length(1,64),Regexp('^[A-Za-z][A-Za-z0-9_]*$',0,u"密码只能包含数字,字母和下划线")])
    password=PasswordField(u"密码",validators=[DataRequired(),EqualTo("password2",message=u"前后输入必须匹配"),Length(1,64)])
    password2=PasswordField(u"再次输入确认密码",validators=[DataRequired(),Length(1,64)])
    submit=SubmitField(u"注册")

    #field 字段继承自FlaskForm
    #如果表单类中定义了validate_开头且后面跟着字段名的方法
    #这个方法就和常规验证函数一起调用 具体如何实现看源码
    def validate_email(self,field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError(u"邮箱已经存在")

    def validate_username(self,field):
        if User.query.filter_by(username=field.data).first():
            raise ValidationError(u"用户名已经存在")

class ChangePasswordForm(FlaskForm):
    old_password = PasswordField(u"旧密码", validators=[DataRequired()])
    password = PasswordField(u"新密码", validators=[DataRequired(), EqualTo('password2', message=u"前后输入必须匹配")])
    #表单中完成密码与确认密码一致性的验证
    password2 = PasswordField(u"确认新密码", validators=[DataRequired()])
    submit = SubmitField(u"更新密码")

#有2个页面产生，一个是让用户输入邮箱并发送邮件的页面
#第二个是你邮箱点击链接返回过来的页面，可以修改密码
class PasswordResetRequestForm(FlaskForm):
    email=StringField(u'邮箱地址',validators=[DataRequired(),Length(1,64),Email()])#提交表单以发送EMAIL
    submit = SubmitField(u'发送')

class PasswordResetForm(FlaskForm):

    email = StringField(u'邮箱地址',validators=[DataRequired(),Email()])   #这一行特别注意，如果没有这一行的话，你到最后路由里面，没有办法定位你的具体账号的。
    newpassword=PasswordField(u'新密码',validators=[DataRequired(),EqualTo('newpassword2',message=u"前后输入必须匹配")])
    newpassword2=PasswordField(u'确认密码',validators=[DataRequired()])
    submit = SubmitField(u'保存更改')

    def validate_email(self, field):                                              #这里前面学过的东西差点又忘记了，以validate_开头的函数，会和普通验证函数一起被调用
        if User.query.filter_by(email=field.data).first() is None:
            raise ValidationError(u'未知邮箱')

