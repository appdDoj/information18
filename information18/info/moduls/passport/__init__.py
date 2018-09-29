from flask import Blueprint

#1.创建蓝图
passport_bp = Blueprint("passport", __name__, url_prefix='/passport')

#3.导入views文件
from  .views import *