from flask import Blueprint

#1.创建蓝图
profile_bp = Blueprint("profile", __name__, url_prefix='/user')

#3.导入views文件
from  .views import *