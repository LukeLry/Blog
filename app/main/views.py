#!/usr/bin/python2.7
# -*- coding: utf-8 -*-

from flask import render_template,session,redirect,url_for,abort,current_app,make_response
from datetime import datetime
from flask_login import login_required,current_user,flash,request
from . import main
from .forms import PostForm,EditProfileForm,EditProfileAdminForm,CommentForm
from .. import db
from ..models import User,Role,Permission,Post,Comment
from ..decorators import admin_required,permission_required
from flask_sqlalchemy import get_debug_queries
import os
from PIL import Image
from werkzeug.utils import secure_filename


#限定文件上传的后缀名
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1] in ["png","jpg","jpeg","gif"]

@main.route("/",methods=["GET","POST"])
def index():

    #编辑并提交博文
    form=PostForm()
    if form.validate_on_submit() and current_user.can(Permission.WRITE_ARTICLES):

        #数据库需要真正的用户对象 current_user由Flask-Login提供
        #和所有上下文变量一样 通过线程内的代理对象实现
        #该对象表现类似用户对象 实际上是一个轻度包装 包含真正的用户对象
        post=Post(body=form.body.data,author=current_user._get_current_object())
        db.session.add(post)
        return redirect(url_for("main.index"))
    #按时间戳降序排列
    #posts=Post.query.order_by(Post.timestamp.desc()).all()

    page=request.args.get('page',1,type=int)

    show_followed=False
    if current_user.is_authenticated():
        show_followed=bool(request.cookies.get('show_followed',''))
    if show_followed:
        query=current_user.followed_posts()
    else:
        query=Post.query

    #返回一个Paginate()对象 该类在SQLAlchemy里面实现
    pagination = query.order_by(Post.timestamp.desc()).paginate(page, per_page=current_app.config['FLASKY_POSTS_PER_PAGE'], error_out=False)
    posts = pagination.items

    return render_template("index.html",form=form,posts=posts,show_followed=show_followed,pagination=pagination)

#解析个人资料页面的视图
@main.route("/user/<username>")
def user(username):
    user=User.query.filter_by(username=username).first()
    if user is None:
        abort(404)

    posts=user.posts.order_by(Post.timestamp.desc()).all()
    return render_template("user.html",user=user,posts=posts)


#普通用户资料编辑路由
@main.route("/edit_profile",methods=["GET","POST"])
@login_required
def edit_profile():
    form=EditProfileForm()
    if form.validate_on_submit():
        current_user.name=form.name.data
        current_user.location=form.location.data
        current_user.about_me=form.about_me.data
    #########
        """"
        if request.method == 'POST':
            file = request.files['file']
            size = (40, 40)
            im = Image.open(file)
            im.thumbnail(size)
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                im.save(os.path.join(current_app.Config["UPLOAD_FOLDER"],filename))
                current_user.avatar = url_for('static', filename='%s/%s' % ('avatar', filename))
                flash(u'头像修改成功')
        """
    #########
        db.session.add(current_user)
        flash(u"你的个人资料已经更新")
        return redirect(url_for("main.user",username=current_user.username))

    form.name.data=current_user.name
    form.location.data=current_user.location
    form.about_me.data=current_user.about_me
    return render_template("edit_profile.html",form=form)

#管理员用户资料编辑路由
@main.route("/edit_profile_admin/<int:id>",methods=["GET","POST"])
@login_required
#自定义装饰器
@admin_required
def edit_profile_admin(id):
    user=User.query.get_or_404(id)
    form=EditProfileAdminForm(user=user)
    if form.validate_on_submit():
        user.email=form.email.data
        user.username=form.username.data
        user.confirmed=form.confirmed.data
        user.role=Role.query.get(form.role.data)
        user.name=form.name.data
        user.location=form.location.data
        user.about_me=form.about_me.data
        db.session.add(user)

        flash(u"你的个人资料已经更新")
        #print("###")
        return redirect(url_for("main.user",username=user.username))

    form.email.data=user.email
    form.username.data=user.username
    form.confirmed.data=user.confirmed
    form.role.data=user.role_id

    form.name.data=user.name

    form.location.data=user.location
    form.about_me.data=user.about_me
    #print("%%%%%")
    return render_template("edit_profile.html",form=form,user=user)

#生成文章固定链接路由
@main.route("/post_blog/<int:id>")
def post_blog(id):
    post=Post.query.get_or_404(id)
    return render_template("post_blog.html",posts=[post])

#编辑博客文章路由
@main.route("/edit/<int:id>",methods=["GET","POST"])
@login_required
def edit(id):
    post=Post.query.get_or_404(id)
    if current_user!=post.author and not current_user.can(Permission.ADMINISTER):
        abort(403)
    form=PostForm()
    if form.validate_on_submit():
        post.body=form.body.data
        db.session.add(post)
        flash(u"博文已经更新")
        return redirect(url_for("main.index",id=post.id))
    form.body.data=post.body
    return render_template("edit_post.html",form=form)

#在某个用户资料页面中 关注某个用户的路由
@main.route('/follow/<username>')
@login_required
@permission_required(Permission.FOLLOW)
def follow(username):
    user=User.query.filter_by(username=username).first()
    if user is None:
        flash(u"用户不存在")
        return redirect(url_for("main.index"))
    if current_user.is_following(user):
        flash(u"你已经关注了该用户")
        return redirect(url_for("main.user",username=username))
    current_user.follow(user)
    flash(u"你已经关注了%s" % username)
    return redirect(url_for("main.user",username=username))

#取消关注
@main.route('/unfollow/<username>')
@login_required
@permission_required(Permission.FOLLOW)
def unfollow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash(u"用户不存在")
        return redirect(url_for('main.index'))
    if not current_user.is_following(user):
        flash(u'你并木有关注这个用户')
        return redirect(url_for('main.user', username=username))
    current_user.unfollow(user)
    db.session.commit()
    flash(u'你已经不再关注%s' % username)
    return redirect(url_for('main.user', username=username))


#在某个用户资料页面中 查看某个用户关注者列表的路由
@main.route('/followers/<username>')
def followers(username):
    user=User.query.filter_by(username=username).first()
    if user is None:
        flash(u"用户不存在")
        return redirect(url_for('main.index'))
    #分页技术显示关注人
    page=request.args.get('page',1,type=int)
    pagination=user.followers.paginate(page,per_page=current_app.config["FLASKY_FOLLOWERS_PER_PAGE"],error_out=False)
    follows=[{"user":item.follower,'timestamp':item.timestamp} for item in pagination.items]
    return render_template('followers.html',user=user,endpoint="main.followers",pagination=pagination,follows=follows)

#在某个用户资料页面中 查看关注这个用户的列表
@main.route('/followed_by/<username>')
def followed_by(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash(u"用户不存在")
        return redirect(url_for('main.index'))
    page = request.args.get('page', 1, type=int)
    pagination = user.followed.paginate(page, per_page=current_app.config['FLASKY_FOLLOWERS_PER_PAGE'],error_out=False)
    follows = [{'user': item.followed, 'timestamp': item.timestamp} for item in pagination.items]
    return render_template('followers.html', user=user,endpoint='main.followed_by', pagination=pagination,follows=follows)

#cookie只能在响应对象中设置 因此该路由使用make_response()方法创建响应对象
@main.route("/show_all")
@login_required
def show_all():
    resp=make_response(redirect(url_for("main.index")))
    resp.set_cookie("show_followed","",max_age=30*24*60*60)
    return resp

@main.route("/show_followed")
@login_required
def show_followed():
    resp=make_response(redirect(url_for("main.index")))
    resp.set_cookie("show_followed","1",max_age=30*24*60*60)
    return resp

#注意和生成博文链接的post路由区分开
@main.route('/post_comment/<int:id>', methods=['GET', 'POST'])
def post_comment(id):
    post = Post.query.get_or_404(id)
    form = CommentForm()
    if form.validate_on_submit():
        comment = Comment(body=form.body.data,post=post,author=current_user._get_current_object())
        db.session.add(comment)
        db.session.commit()
        flash(u'你的评论已经发出')
        return redirect(url_for('main.post_comment', id=post.id, page=-1))
    page = request.args.get('page', 1, type=int)
    if page == -1:
        page = (post.comments.count() - 1) // current_app.config['FLASKY_COMMENTS_PER_PAGE'] + 1
    pagination = post.comments.order_by(Comment.timestamp.asc()).paginate(page, per_page=current_app.config['FLASKY_COMMENTS_PER_PAGE'],error_out=False)
    comments = pagination.items
    return render_template('post_comment.html', posts=[post], form=form,comments=comments, pagination=pagination)


@main.route('/moderate')
@login_required
@permission_required(Permission.MODERATE_COMMENTS)
def moderate():
    page = request.args.get('page', 1, type=int)
    pagination = Comment.query.order_by(Comment.timestamp.desc()).paginate(page, per_page=current_app.config['FLASKY_COMMENTS_PER_PAGE'],error_out=False)
    comments = pagination.items
    return render_template('moderate.html', comments=comments,pagination=pagination, page=page)

@main.route('/moderate/enable/<int:id>')
@login_required
@permission_required(Permission.MODERATE_COMMENTS)
def moderate_enable(id):
    comment = Comment.query.get_or_404(id)
    comment.disabled = False
    db.session.add(comment)
    db.session.commit()
    return redirect(url_for('.moderate',page=request.args.get('page', 1, type=int)))


@main.route('/moderate/disable/<int:id>')
@login_required
@permission_required(Permission.MODERATE_COMMENTS)
def moderate_disable(id):
    comment = Comment.query.get_or_404(id)
    comment.disabled = True
    db.session.add(comment)
    db.session.commit()
    return redirect(url_for('.moderate',page=request.args.get('page', 1, type=int)))


#使用Selenium进行测试要求程序在Web服务器中运行 监听真实的HTTP请求
#让程序运行在后台线程里的开发服务器中 测试程序运行在主线程中      ?????????
@main.route('/shutdown')
def server_shutdown():
    #只有在当程序运行在测试环境中 这个关闭服务器的路由才可以调用
    if not current_app.testing:
        abort(404)
    #关闭服务器时要调用Werkzeug在环境中提供的关闭函数
    shutdown = request.environ.get('werkzeug.server.shutdown')
    if not shutdown:
        abort(500)
    shutdown()
    return u'正在关闭服务器'

#在生产环境中分析数据库性能
#在视图函数处理完请求之后
#flask把响应对象传给after_app_request处理程序
@main.after_app_request
def after_app_request(response):
    #get_debug_queries()返回一个列表 其元素是请求中执行的查询
    for query in get_debug_queries():
        if query.duration >= current_app.config['FLASKY_SLOW_DB_QUERY_TIME']:
            #将缓慢查询写入日志
            #写入的日志被设置为"警告"等级
            current_app.logger.warning(
                'Slow query: %s\nParameters: %s\nDuration: %fs\nContext: %s\n' % (query.statement,query.parameters,query.duration,query.context)

            )
    return response

