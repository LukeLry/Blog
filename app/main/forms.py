# -*- coding: utf-8 -*-
from flask_wtf import FlaskForm
from wtforms import StringField,SubmitField,TextAreaField,BooleanField,SelectField,FileField
from wtforms.validators import DataRequired,Length,Email,Regexp,ValidationError
from flask_wtf.file import FileRequired,FileAllowed
from ..models import User,Role
from flask_pagedown.fields import PageDownField

#编辑用户资料的页面
class EditProfileForm(FlaskForm):
    name=StringField(u"真实姓名",validators=[Length(0,64)])
    location=StringField(u"住址",validators=[Length(0,64)])
    about_me=TextAreaField(u"关于我")
    #avatar=FileField(u"头像",validators=[FileRequired(message=u"请选择文件")])
    submit=SubmitField(u"提交")

#管理员使用的资料编辑
class EditProfileAdminForm(FlaskForm):
    #管理员能编辑电子邮件,用户名，确认状态和角色
    email=StringField(u"邮箱",validators=[DataRequired(),Length(1,64),Email()])
    username=StringField(u"用户名",validators=[DataRequired(),Length(1,64),Regexp('^[A-Za-z][A-Za-z0-9_]*$',0,u"用户名只能包含数字,字母和下划线")])

    confirmed=BooleanField(u"是否已经确认账户")

    #WTFforms对HTML表单控件<select>进行Selected包装
    #实现下拉列表 coerce=int 将字段的值转换为整数,而不使用默认的字符串
    role=SelectField(u"角色",coerce=int)

    name=StringField(u"真实姓名",validators=[Length(0,64)])
    location=StringField(u"地址",validators=[Length(0,64)])
    about_me=TextAreaField(u"关于我")
    submit=SubmitField(u"提交")

    #表单构造函数接收用户对象作为参数,并将其保存在成员变量中,随后自定义的验证方法要使用这个用户对象
    def __init__(self,user,*args,**kwargs):
        super(EditProfileAdminForm,self).__init__(*args,**kwargs)

        #Selected实例必须在其choices属性中设置各选项
        self.role.choices=[(role.id,role.name) for role in Role.query.order_by(Role.name).all()]
        self.user=user

    #验证username和email两个字段时,首先要检查字段的值是否发生了变化,如果有变化，就要保证新值不和其他用户相应字段重复
    #如果字段值没有发生变化,则应该跳过验证
    def validate_email(self,field):
        if field.data!=self.user.email and User.query.filter_by(email=field.data).first():
            raise ValidationError(u"邮箱已经存在")

    def validate_username(self,field):
        if field.data!=self.user.username and User.query.filter_by(username=field.data).first():
            raise ValidationError(u"用户名已经存在")


class PostForm(FlaskForm):
    #Flask-PageDown扩展定义了一个PageDownField类
    #用PageDown替代TextAreaField 和TextAreaField接口一致
    #body=TextAreaField(u"编辑你的博文",validators=[DataRequired()])
    body = PageDownField(u"编辑你的博文", validators=[DataRequired()])
    submit=SubmitField(u"提交")

class CommentForm(FlaskForm):
    body=StringField('',validators=[DataRequired()])
    submit=SubmitField(u"添加评论")



