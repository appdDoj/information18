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


import functools


def user_login_data(view_func):
    """用户登录成功的装饰器"""
    # 使用装饰器会修改函数的一些特有属性，为了防止这一现象，使用该装饰器解决
    @functools.wraps(view_func)
    def wrapper(*args, **kwargs):
        result = view_func(*args, **kwargs)
        return result
    return wrapper


@user_login_data
def index():
    """index"""
    print("index")

@user_login_data
def user():
    """user"""
    print("user")


if __name__ == '__main__':
    print(index.__name__)
    print(user.__name__)