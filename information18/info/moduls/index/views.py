import logging
from flask import current_app, render_template, session, jsonify
from info.utits.response_code import RET
from . import index_bp
from info import redis_store
from info.models import User


#2. 使用蓝图
@index_bp.route('/')
def hello_world():
    # 返回模板文件
    print(current_app.url_map)
    #1.获取用户id
    user_id = session.get("user_id")
    # 用户id有值才去查询用户数据
    user = None # type: User
    if user_id:
        try:
            user = User.query.get(user_id)
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.DBERR, errmsg="查询用户对象异常")

    """
    if user:
        # user：对象 --> 字典
        user_info = user.to_dict()

    #数据格式：
    data= {
        "user_info"： {"id": self.id}
    }

    #在模板中获取方法
    data.user_info.nick_name: 获取用户昵称
    """
    data = {
        "user_info": user.to_dict() if user else None,
    }

    return render_template("news/index.html",data=data)


# 浏览器默认会往这个路径发送请求获取网站图片（定时请求）
@index_bp.route('/favicon.ico')
def favicon():
    """返回网站图标"""
    """
    Function used internally to send static files from the static
        folder to the browser
    # 内部发送静态文件函数，将static文件夹下的静态文件发送到浏览器
    """
    return current_app.send_static_file('news/favicon.ico')