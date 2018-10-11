from flask import Blueprint

#1.创建蓝图对象
news_bp = Blueprint("news", __name__, url_prefix='/news')

#3.导入views文件
from .views import *