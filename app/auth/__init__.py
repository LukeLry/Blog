# -*- encoding=UTF-8 -*-
from flask import Blueprint

#创建认证蓝本 用于管理所有认证视图
auth=Blueprint("auth",__name__)

from . import views
