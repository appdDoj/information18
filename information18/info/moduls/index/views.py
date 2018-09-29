import logging
from flask import current_app, render_template
from . import index_bp
from info import redis_store
from info.models import User


#2. 使用蓝图
@index_bp.route('/')
def hello_world():
    # 返回模板文件
    print(current_app.url_map)
    return render_template("news/index.html")


@index_bp.route('/favicon.ico')
def favicon():
    """返回网站图标"""
    """
    Function used internally to send static files from the static
        folder to the browser
    # 内部发送静态文件函数，将static文件夹下的静态文件发送到浏览器
    """
    return current_app.send_static_file('news/favicon.ico')