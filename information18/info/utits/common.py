from flask import current_app, jsonify
from flask import session, g
from info.utits.response_code import RET


def do_index_class(index):
    """根据index下标返回不同class"""
    if index == 1:
        return "first"
    elif index == 2:
        return "second"
    elif index == 3:
        return "third"
    else:
        return ""

import functools


def user_login_data(view_func):
    """用户登录成功的装饰器"""

    @functools.wraps(view_func)
    def wrapper(*args, **kwargs):
        # 1 装饰器要实现的功能
        # 1.获取用户id
        user_id = session.get("user_id")
        # 用户id有值才去查询用户数据
        user = None  # type: User
        # 延迟导入，解决db循环导入问题
        from info.models import User
        if user_id:
            try:
                user = User.query.get(user_id)
            except Exception as e:
                current_app.logger.error(e)
                return jsonify(errno=RET.DBERR, errmsg="查询用户对象异常")
        # 将查询出来到用户对象保存到g对象
        g.user = user
        # 2 原有函数的功能实现
        result = view_func(*args, **kwargs)
        return result
    return wrapper