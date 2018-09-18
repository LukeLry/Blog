# -*- coding: utf-8 -*-
from flask import jsonify, request, g, url_for, current_app
from .. import db
from ..models import Post, Permission
from . import api
from .decorators import permission_required
from flask import jsonify,g
from .errors import forbidden

@api.route('/posts/', methods=['POST'])
#确保通过认证的用户有能写文章的权利
@permission_required(Permission.WRITE_ARTICLES)
#创建新博文的路由 创建资源成功后返回
def new_post():
    #博客文章内容以json格式编码 静态函数from_json获取文章的body
    #请求中包含的JSON数据可以通过request.json这个Python字典获取

    #g在一个请求中共享变量 不同的g对象对应是不同的g对象 单个request处理完 g清空
    #session对象用于在不同请求之间共享变量 session的数据经过密钥加密后存储在cookie中并发送给客户端 客户端再次请求的时候又带上cookie
    #用户每次request都会将这些信息发回来 从而实现跨request使用

    post = Post.from_json(request.json)
    #处理请求时临时存储的对象 每次请求都会重置这个变量
    post.author = g.current_user
    db.session.add(post)
    db.session.commit()
    #需要包含JSON的响应使用Flask提供的辅助函数jsonify()从python字典中生成
    #该模型写入数据库之后 返回201状态码 并把Location首部的值设为刚创建的这个资源的URL
    return jsonify(post.to_json()), 201, {'Location': url_for('api.get_post', id=post.id)}

#获取所有博文列表
@api.route('/posts/')
def get_posts():
    page=request.args.get('page',1,type=int)
    pagination=Post.query.paginate(page,per_page=current_app.config['FLASKY_POSTS_PER_PAGE'],error_out=False)
    posts=pagination.items

    prev=None
    if pagination.has_prev:
        pre=url_for('api.get_posts',page=page-1,_external=True)
    next=None
    if pagination.has_next:
        next=url_for('api.get_posts',page=page+1,_external=True)

    return jsonify(
        {
            'posts':[post.to_json() for post in posts],
            'prev':prev,
            'next':next,
            'count':pagination.total
        }
    )

    #posts=Post.query.all()
    #return jsonify({'posts':[post.to_json() for post in posts]})

#获取某一篇博文
@api.route('/posts/<int:id>')
def get_post(id):
    post=Post.query.get_or_404(id)
    return jsonify(post.to_json())

#编辑博文
@api.route('/posts/<int:id>',methods=['PUT'])
@permission_required(Permission.WRITE_ARTICLES)
def edit_post(id):
    post=Post.query.get_or_404(id)
    #保证该用户是作者或者是管理员
    if g.current_user!=post.author and not g.current_user.can(Permission.ADMINISTER):
        return forbidden(u'权限不够')
    post.body=request.json.get('body',post.body)
    db.session.add(post)
    return jsonify(post.to_json())


