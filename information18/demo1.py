# class Person(object):
#
#     def __init__(self):
#         self.name = "hh"
#
#     def __eq__(self, other):
#         return "哈哈"
#
#
# if __name__ == '__main__':
#     p1 = Person()
#     p2 = Person()
#     print(p1 == p2)




# import functools
#
#
# def user_login_data(view_func):
#     """用户登录成功的装饰器"""
#     # 使用装饰器会修改函数的一些特有属性，为了防止这一现象，使用该装饰器解决
#     @functools.wraps(view_func)
#     def wrapper(*args, **kwargs):
#         result = view_func(*args, **kwargs)
#         return result
#     return wrapper
#
#
# @user_login_data
# def index():
#     """index"""
#     print("index")
#
# @user_login_data
# def user():
#     """user"""
#     print("user")
#
#
# if __name__ == '__main__':
#     print(index.__name__)
#     print(user.__name__)


import datetime
import random

from info import db
from info.models import User
from manage import app


def add_test_users():
    """录入一万个用户数据"""

    users = []
    # 获取当前实际
    now = datetime.datetime.now()
    for num in range(0, 10000):
        try:
            user = User()
            user.nick_name = "%011d" % num
            user.mobile = "%011d" % num
            user.password_hash = "pbkdf2:sha256:50000$SgZPAbEj$a253b9220b7a916e03bf27119d401c48ff4a1c81d7e00644e0aaf6f3a8c55829"
            # now：当前时间节点，
            # datetime.timedelta(seconds=random.randint(0, 2678400): 一个月的随机秒数
            # 从当前时间节点往前推一个月，在这个一个月中的随机登录时间（9-11 00:00  --  10:11:24:00）
            user.last_login = now - datetime.timedelta(seconds=random.randint(0, 2678400))
            users.append(user)
        except Exception as e:
            print(e)
    # 手动开启应用上下文
    with app.app_context():
        db.session.add_all(users)
        db.session.commit()
    print("OK")

if __name__ == '__main__':
    add_test_users()