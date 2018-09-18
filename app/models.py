# -*- encoding=UTF-8 -*-
from app import db
from flask_login import UserMixin,AnonymousUserMixin
from . import login_manager
from werkzeug.security import generate_password_hash,check_password_hash
from flask import current_app,request,url_for
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from . import db
from datetime import datetime
import hashlib
import os
from markdown import markdown
import bleach
from app.exceptions import ValidationError


#程序权限
class Permission:
    FOLLOW=0x01                 #关注者
    COMMENT=0x02                #在他人的文章中发表评论
    WRITE_ARTICLES=0x04         #写文章
    MODERATE_COMMENTS=0x08      #管理他人发表的文章
    ADMINISTER=0x10             #管理员权限


class Role(db.Model):
    __tablename__="roles"
    id=db.Column(db.Integer,primary_key=True)
    name=db.Column(db.String(64),unique=True)
    default=db.Column(db.Boolean,default=False,index=True)      #只有一个角色的字段要设为True,其它都为False
    permissions=db.Column(db.Integer)                           # 不同角色的权限不同

    #对于一个Role实例 其user属性将返回与角色相关联的用户组成的列表 db.relationship()的第一个参数表明另一段是哪个模型
    #backref参数向User模型中添加一个role属性从而定义反定向关系 这一属性可代替role_id访问Role模型 此时获取的是模型对象 而不是外键的值
    #lazy决定了什么时候从数据库中加载数据
    #select 访问到属性到属性的时候 全部加载该属性的数据 返回结果列表
    #joined则是在对关联的两个表进行join操作 从而获取所有相关的对象
    #dynamic 在访问属性的时候 并没有在内存中加载数据 而是返回一个query对象 需要执行相应方法才可以获取对象
    #lazy="dynamic"只可以用在一对多和多对多关系中，不可以用在一对一和多对一中
    #dynamic返回一个查询对象 而不是直接生成列表 可以在上面直接进行操作
    #dynamic在访问属性的时候 并没有在内存中加载数据 而是返回一个query对象 需要执行相应方法才可以获取对象 比如.all().
    #backref的lazy默认都是select 如果给反向引用backref加lazy属性呢? 直接使用backref=db.backref('students', lazy='dynamic'即可
    #这个在多对多关系需要进行考量
    #http://shomy.top/2016/08/11/flask-sqlalchemy-relation-lazy/

    users=db.relationship("User",backref="role",lazy="dynamic")

    #记得把角色写进数据库！！！！！！！！！！
    @staticmethod
    def insert_roles():
        roles={
            u"用户":(Permission.FOLLOW|Permission.COMMENT|Permission.WRITE_ARTICLES,True),
            u"协管员":(Permission.FOLLOW|Permission.COMMENT|Permission.WRITE_ARTICLES|Permission.MODERATE_COMMENTS,False),
            u"管理员":(Permission.FOLLOW|Permission.COMMENT|Permission.WRITE_ARTICLES|Permission.MODERATE_COMMENTS|Permission.ADMINISTER,False)
        }
        for r in roles:
            role=Role.query.filter_by(name=r).first()           #确保数据库中有该角色
            if role is None:
                role=Role(name=r)
            role.permissions=roles[r][0]
            role.default=roles[r][1]
            db.session.add(role)
        db.session.commit()


    def __repr__(self):
        return "<Role %r>" % self.name

#处理关注和被关注
class Follow(db.Model):
    __tablename__ = 'follows'
    follower_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    followed_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

#Flask-login模型的四种方法 UserMixin
#is_authenticated()
#is_active()
#is_anonymous()
#get_id()
class User(UserMixin,db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    email=db.Column(db.String(64), unique=True,index=True)           #用户实现电子邮件的登陆
    username = db.Column(db.String(64), unique=True,index=True)

    #在User模型中role_id列被定义为外键 该外键的值为Role模型中方的id值
    role_id=db.Column(db.Integer,db.ForeignKey("roles.id"))
    password_hash=db.Column(db.String(128))

    posts=db.relationship("Post",backref="author",lazy="dynamic")

    comments = db.relationship('Comment', backref='author', lazy='dynamic')

    #新增用户头像
    #avatar=db.Column(db.String(200),default=None)

    #第一个password(self)是get方法 用@property装饰 第二个password(self, score)是set方法 用@password.setter装饰
    #@password.setter是前一个@property装饰后的副产品
    #可以像简单取值和赋值操作一样操作password
    @property
    def password(self):
        raise AttributeError(u"密码不是一个可读的属性")

    @password.setter
    def password(self,password):
        self.password_hash=generate_password_hash(password)

    def verify_password(self,password):
        return check_password_hash(self.password_hash,password)

    avatar_hash=None
    def __init__(self,**kwargs):                                    #User类的构造函数首先调用基类的构造函数
        super(User,self).__init__(**kwargs)
        if self.role is None:
            if self.email==current_app.config["FLASKY_ADMIN"]:      #管理员角色
                self.role=Role.query.filter_by(permissions=0x1f).first()
            if self.role is None:                                   #普通角色
                self.role=Role.query.filter_by(default=True).first()
            if self.email is not None and self.avatar_hash is None:
                self.avatar_hash=hashlib.md5(self.email.encode('utf-8')).hexdigest()
        # 自己关注自己
        #self.follow(self)



    confirmed=db.Column(db.Boolean,default=False)

    def generate_confirmation_token(self,expiration=3600):
        #TimedJSONWebSignatureSerializer类(Serializer)生成具有过期时间的JSON Web签名
        s=Serializer(current_app.config["SECRET_KEY"],expiration)
        #dumps()方法为指定的数据生成一个加密签名 即token值
        return s.dumps({"confirm":self.id})

    def confirm(self,token):
        s=Serializer(current_app.config["SECRET_KEY"])
        try:
            #为了解码令牌 序列化对象提供了loads()方法 参数是令牌字符串 token值
            data=s.loads(token)
        except:
            #print("%%%")
            return False

        if data.get("confirm")!=self.id:
            #print("###")
            return False

        self.confirmed=True
        db.session.add(self)
        return True

#只是对于重新设置密码这个功能来说 需要自己新建一个的 因为confirm里面最后的目标是修改confirmed属性
# 而我们这里不需要，我们最终目标是修改密码
    def generate_reset_password_token(self, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'reset': self.id})

    def reset_password(self, token, new_password):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return False
        #同一个id经过加密后会生成不同的token 每个token有不同的用途 其实使用confirm token也没有问题
        if data.get('reset') != self.id:
            return False
        self.password = new_password  # 这里隐式的调用了password.setter的装饰器 来重新设定密码
        db.session.add(self)
        return True

    def can(self,permissions):                                          #检查用户的权限 位运算的应用
        return self.role is not None and (self.role.permissions & permissions) ==permissions

    def is_administrator(self):                                         #检查是否为管理者
        return self.can(Permission.ADMINISTER)

    #用户信息字段
    name=db.Column(db.String(64))
    location=db.Column(db.String(64))
    about_me=db.Column(db.Text())
    member_since=db.Column(db.DateTime(),default=datetime.utcnow)
    last_seen=db.Column(db.DateTime(),default=datetime.utcnow)

    #刷新用户最后访问的时间
    def ping(self):
        self.last_seen=datetime.utcnow()
        db.session.add(self)

    def gravatar(self, size=100, default='identicon', rating='g'):
        if request.is_secure:   # 判断是否是https
            url = 'https://secure.gravatar.com/avatar'
        else:
            url = 'http://www.gravatar.com/avatar'
        hash = self.avatar_hash or hashlib.md5(self.email.encode('utf-8')).hexdigest()

        #生成图片URL
        return '{url}/{hash}?s={size}&d={default}&r={rating}'.format(url=url, hash=hash, size=size, default=default, rating=rating)

    @staticmethod
    def generate_fake(count=100):
        from sqlalchemy.exc import IntegrityError
        from random import seed
        import forgery_py

        seed()
        for i in range(count):
            u=User(email=forgery_py.internet.email_address(),
                   username=forgery_py.internet.user_name(True),
                   password=forgery_py.lorem_ipsum.word(),
                   confirmed=True,
                   name=forgery_py.name.full_name(),
                   location=forgery_py.address.city(),
                   about_me=forgery_py.lorem_ipsum.sentence(),
                   member_since=forgery_py.date.date(True))
            db.session.add(u)
            #若生成重复信息 则实现数据库回滚
            try:
                db.session.commit()
            except IntegrityError:
                db.session.rollback()

    #把用户设为自己的关注着
    @staticmethod
    def add_self_follows():
        for user in User.query.all():
            if not user.is_following(user):
                user.follow(user)
                db.session.add(user)
                db.session.commit()

    followed = db.relationship('Follow',
                               foreign_keys=[Follow.follower_id],
                               backref=db.backref('follower', lazy='joined'),
                               lazy='dynamic',
                               #lazy='subquery',
                               cascade='all, delete-orphan')
    followers = db.relationship('Follow',
                                foreign_keys=[Follow.followed_id],
                                backref=db.backref('followed', lazy='joined'),
                                lazy='dynamic',
                                #lazy='subquery',
                                cascade='all, delete-orphan')
    #关注某个用户user
    def follow(self,user):
        if not self.is_following(user):
            f=Follow(follower=self,followed=user)
            db.session.add(f)

    #取关某个用户user
    def unfollow(self,user):
        f=self.followed.filter_by(followed_id=user.id).first()
        if f:
            db.session.delete(f)

    #判断是否关注了某个用户
    def is_following(self,user):
        return self.followed.filter_by(followed_id=user.id).first() is not None

    #判断是否被某个用户关注
    def is_followed_by(self,user):
        return self.followers.filter_by(follower_id=user.id).first() is not None

    #获取所关注用户的文章列表
    def followed_posts(self):
        #先连结再过滤
        #SELECT posts.id AS posts_id, posts.body AS posts_body, posts.timestamp AS posts_timestamp, posts.author_id AS posts_author_id, posts.body_html AS posts_body_html
        #FROM users, posts JOIN follows ON follows.followed_id = posts.author_id
        #WHERE follows.follower_id = users.id

        return Post.query.join(Follow,Follow.followed_id==Post.author_id).filter(Follow.follower_id==self.id)

    #为了避免频繁给REST　API发送认证密令 使用基于令牌的认证方案
    #可以简单的看成将ID值做一次哈希 密钥是SECRETE_KEY
    def generate_auth_token(self,expiration):
        s=Serializer(current_app.config['SECRET_KEY'],expires_in=expiration)
        return s.dumps({'id':self.id})

    @staticmethod
    def verify_auth_token(token):
        s=Serializer(current_app.config['SECRET_KEY'])
        try:
            data=s.loads(token)
        except:
            return None
        #解密后得到用户的ID
        return User.query.get(data['id'])

    def to_json(self):
        #email属性和role没有加入响应
        #提供给客户端的资源表示没必要和数据库模型的内部表示完全一致
        json_user={
            'url':url_for('api.get_user',id=self.id,_external=True),
            'username':self.username,
            'member_since':self.member_since,
            'last_since':self.last_seen,
            'posts':url_for('api.get_user_posts',id=self.id,_external=True),
            #关注者的博文
            'followed_posts':url_for('api.get_user_followed_posts',id=self.id,_external=True),
            #该用户的博文数量
            'post_count':self.posts.count()
        }
        return json_user

    def __repr__(self):
        return "<User %r>" % self.username


#AnonymousUser对象继承自Flask-Login中的AnonymousUserMixin
#并将其设为用户未登陆时current_user值
#这样程序不用先检查用户是否登陆 就能调用current_user.can() current_user.adminstraAnonymousUserMixintor()
class AnonymousUser(AnonymousUserMixin):
    def can(self,permissions):
        return False

    def is_administrator(self):
        return False

login_manager.anonymous_user=AnonymousUser


#由于HTTP是无状态连接 每次发起新请求时flask 会创建一个请求上下文
#在分发路由时flask-login根据cookie判断用户并绑定到当前的请求上下文
#由于这种绑定关系的存在 那么每次新的请求发生时都需要获取user
#提供user_loader的回调函数 主要是通过获取user对象存储到session中
#https://segmentfault.com/a/1190000015123733
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class Post(db.Model):
    __tablename__ = "posts"
    id=db.Column(db.Integer,primary_key=True)
    body=db.Column(db.Text)
    timestamp=db.Column(db.DateTime,index=True,default=datetime.utcnow)
    author_id=db.Column(db.Integer,db.ForeignKey("users.id"))

    body_html=db.Column(db.Text)

    comments = db.relationship('Comment', backref='post', lazy='dynamic')

    #生成虚假数据用于测试
    @staticmethod
    def generate_fake(count=100):
        from random import seed,randint
        import forgery_py
        seed()
        user_count=User.query.count()
        for i in range(count):
            u=User.query.offset(randint(0,user_count-1)).first()
            p=Post(body=forgery_py.lorem_ipsum.sentences(randint(1,3)),
                   timestamp=forgery_py.date.date(True),
                   author=u)
            db.session.add(p)
            db.session.commit()

    #json和资源的序列化转换
    def to_json(self):
        #在资源的内部表示和JSON之间转换
        #url author comments字段要分别返回各自资源的URL
        #所调用的URL在API蓝本中定义 生成完整的URL 并非相对URL
        json_post={
            'url':url_for('api.get_post',id=self.id,_external=True),
            'body':self.body,
            'body_html':self.body_html,
            'timestamp':self.timestamp,
            'author':url_for('api.get_user',id=self.author_id,_external=True),
            'comments':url_for('api.get_post_comments',id=self.id,_external=True),
            #表示资源时可以使用虚构属性 comment_count字段是文章评论数量而不是模型真实的属性
            'comment_count':self.comments.count()
        }
        return json_post

    @staticmethod
    def from_json(json_post):
        body=json_post.get('body')
        if body is None or body == '':
            raise ValidationError(u"该博文没有内容")
        return Post(body=body)
    #body_html注册在on_changed_body SQLAlchemy被触发后自动生成
    #comment和comment_count属性使用数据库关系自动生成
    #author字段是当前通过认证的用户
    #timestamp不需要生成??

##############################################################
    @staticmethod
    def on_changed_body(target, value, oldvalue, initiator):
        allowed_tags = ['a', 'abbr', 'acronym', 'b', 'blockquote', 'code',
                        'em', 'i', 'li', 'ol', 'pre', 'strong', 'ul',
                        'h1', 'h2', 'h3', 'p']
        target.body_html = bleach.linkify(bleach.clean(markdown(value, output_format='html'),tags=allowed_tags, strip=True))
###############################################################

#on_changed_body函数注册在body字段上 只要body属性发生变化 就会触发一个SQLAlchemy事件 自动在服务端渲染Markdown 生成body_html
db.event.listen(Post.body,'set',Post.on_changed_body)


class Comment(db.Model):
    __tablename__='comments'
    id=db.Column(db.Integer,primary_key=True)
    body=db.Column(db.Text)
    body_html=db.Column(db.Text)
    timestamp=db.Column(db.DateTime,index=True,default=datetime.utcnow)
    disabled=db.Column(db.Boolean)

    #评论和博客 用户一对多的关系
    author_id=db.Column(db.Integer,db.ForeignKey('users.id'))
    post_id=db.Column(db.Integer,db.ForeignKey('posts.id'))



    @staticmethod
    def on_changed_body(target, value, oldvalue, initiator):
        allowed_tags = ['a', 'abbr', 'acronym', 'b', 'code','em', 'i','strong']
        target.body_html = bleach.linkify(bleach.clean(markdown(value, output_format='html'), tags=allowed_tags, strip=True))

    #和博客文章一样 评论也定义了一个事件 在修改body字段内容时容易触发 自动把MarkDown文本转换未HTML
db.event.listen(Comment.body,'set',Comment.on_changed_body)



