# -*- coding: utf-8 -*-
from flask import Blueprint
main=Blueprint("main",__name__)

from ..models import Permission
from . import views,errors

#在模板中可能也检查权限
#为了避免每次调用render_template()时都添加一个参数 可以使用上下文处理器
#上下文处理器可以使得在所有模板中全局中可访问
#上下文处理器也就是把全局变量进行封装然后展现到模板当中
#用它传递变量和方法给所有的模板使用 比较广告 头部 底部一些共用的地方可能会需要调用一些动态数据
#而又不可能把每个路由就写一遍 这个时候上下文处理器就派上用场
@main.app_context_processor
def inject_permissions():
    return dict(Permission=Permission)
